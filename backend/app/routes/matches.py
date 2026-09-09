from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.database.supabase import (
    supabase,
)

from app.database.auth_dependency import (
    get_current_user,
)

from app.services.project_knowledge_service import (
    get_project_knowledge,
    learn_from_planner_correction,
)

from ai.extraction.extractor import (
    ExtractedFieldEvent,
    extract_field_event,
)

from ai.matching.reconciliation_engine import (
    rank_with_reconciliation,
)

from ai.matching.confidence_gate import (
    evaluate_match_guardrail,
)

from ai.progress.physical_progress import (
    calculate_physical_progress,
)


router = APIRouter(
    prefix="/matches",
    tags=["Activity Matching"],
)


# -------------------------------------------------------------------
# Authorization
# -------------------------------------------------------------------

def require_reviewer(
    current_user: dict = Depends(
        get_current_user
    ),
):
    role = (
        current_user
        .get("profile", {})
        .get("role")
    )

    if role not in [
        "planner",
        "reviewer",
    ]:
        raise HTTPException(
            status_code=403,
            detail=(
                "Planner or reviewer "
                "access required."
            ),
        )

    return current_user


# -------------------------------------------------------------------
# Activity retrieval
# -------------------------------------------------------------------

def get_all_project_activities(
    project_id: str,
) -> list[dict]:

    all_activities = []

    offset = 0
    batch_size = 1000

    while True:

        response = (
            supabase
            .table("activities")
            .select("*")
            .eq(
                "project_id",
                project_id,
            )
            .range(
                offset,
                offset
                + batch_size
                - 1,
            )
            .execute()
        )

        rows = (
            response.data
            or []
        )

        all_activities.extend(
            rows
        )

        if len(rows) < batch_size:
            break

        offset += batch_size

    return all_activities


# -------------------------------------------------------------------
# Stored Extraction
# -------------------------------------------------------------------

def get_or_create_stored_extraction(
    event: dict,
) -> ExtractedFieldEvent:
    """
    Return the persisted structured extraction for a field event.

    A field update should be interpreted only once whenever possible.

    New field events:
        matching extracts -> stores extracted_data -> all later stages reuse it.

    Historical field events:
        if extracted_data is missing, extract once and persist it for all
        future operations.
    """

    stored_extraction = (
        event.get(
            "extracted_data"
        )
    )

    if stored_extraction:

        return ExtractedFieldEvent(
            **stored_extraction
        )

    raw_text = (
        event.get(
            "raw_text"
        )
        or ""
    )

    extracted = (
        extract_field_event(
            raw_text
        )
    )

    extracted_dict = (
        extracted.model_dump()
    )

    (
        supabase
        .table("field_events")
        .update(
            {
                "extracted_data":
                    extracted_dict,
            }
        )
        .eq(
            "id",
            event["id"],
        )
        .execute()
    )

    # Keep current in-memory event synchronized
    # so downstream functions in the same request
    # do not need to query the database again.
    event[
        "extracted_data"
    ] = extracted_dict

    print(
        "[EXTRACTION] Persisted structured extraction:",
        event["id"],
    )

    return extracted


# -------------------------------------------------------------------
# Execution Event + Physical Progress
# -------------------------------------------------------------------

def create_execution_event_from_match(
    event: dict,
    match: dict,
):

    field_event_id = event["id"]
    activity_id = match["activity_id"]

    # ---------------------------------------------------------------
    # Duplicate protection
    # ---------------------------------------------------------------

    duplicate_response = (
        supabase
        .table("execution_events")
        .select("*")
        .eq(
            "field_event_id",
            field_event_id,
        )
        .eq(
            "activity_id",
            activity_id,
        )
        .limit(1)
        .execute()
    )

    if duplicate_response.data:

        existing_execution_event = (
            duplicate_response.data[0]
        )

        print(
            "[EXECUTION EVENT] Duplicate prevented:",
            existing_execution_event.get(
                "id"
            ),
        )

        return existing_execution_event

    # ---------------------------------------------------------------
    # Get matched activity
    # ---------------------------------------------------------------

    activity_response = (
        supabase
        .table("activities")
        .select("*")
        .eq(
            "id",
            activity_id,
        )
        .limit(1)
        .execute()
    )

    if not activity_response.data:
        raise HTTPException(
            status_code=404,
            detail="Activity not found.",
        )

    activity = (
        activity_response.data[0]
    )

    # ---------------------------------------------------------------
    # Reuse persisted extraction
    # ---------------------------------------------------------------

    extracted = (
        get_or_create_stored_extraction(
            event
        )
    )

    # ---------------------------------------------------------------
    # Physical Progress Engine
    # ---------------------------------------------------------------

    progress_result = (
        calculate_physical_progress(
            activity=activity,
            extracted=extracted,
        )
    )

    print(
        "[PHYSICAL PROGRESS]",
        progress_result,
    )

    # ---------------------------------------------------------------
    # Execution event
    # ---------------------------------------------------------------

    execution_type = (
        extracted.progress_state
        or extracted.work_type
        or "field_activity"
    )

    execution_name = (
        activity.get(
            "activity_name"
        )
        or activity.get(
            "name"
        )
        or "Field Activity"
    )

    execution_payload = {
        "project_id":
            event["project_id"],

        "activity_id":
            activity_id,

        "field_event_id":
            field_event_id,

        "execution_type":
            execution_type,

        "execution_name":
            execution_name,

        "quantity":
            extracted.quantity,

        "unit":
            extracted.unit,

        "progress_contribution":
            progress_result[
                "progress_contribution"
            ],

        "progress_method":
            progress_result.get(
                "method"
            ),

        "status":
            "verified",
    }

    execution_response = (
        supabase
        .table("execution_events")
        .insert(
            execution_payload
        )
        .execute()
    )

    execution_event = None

    if execution_response.data:

        execution_event = (
            execution_response.data[0]
        )

    # ---------------------------------------------------------------
    # Update activity progress / quantity / status
    # ---------------------------------------------------------------

    activity_update = {}

    if progress_result[
        "should_update_progress"
    ]:

        activity_update[
            "actual_progress"
        ] = progress_result[
            "new_progress"
        ]

    if progress_result[
        "should_update_quantity"
    ]:

        activity_update[
            "actual_quantity"
        ] = progress_result[
            "new_quantity"
        ]

    current_progress = float(
        progress_result.get(
            "new_progress",
            activity.get(
                "actual_progress"
            )
            or 0,
        )
        or 0
    )

    progress_state = (
        extracted.progress_state
    )

    # ---------------------------------------------------------------
    # Status handling
    # ---------------------------------------------------------------

    if progress_state:

        normalized_state = (
            progress_state
            .strip()
            .lower()
        )

        if normalized_state in [
            "started",
            "in_progress",
        ]:

            if not activity.get(
                "actual_start"
            ):

                activity_update[
                    "actual_start"
                ] = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

            if current_progress < 100:

                activity_update[
                    "status"
                ] = "in_progress"

        elif (
            normalized_state
            == "blocked"
        ):

            activity_update[
                "status"
            ] = "delayed"

        elif (
            normalized_state
            == "completed"
        ):

            # Example:
            # "45% completed"
            # must NOT mark the entire activity
            # as fully completed.

            if not activity.get(
                "actual_start"
            ):

                activity_update[
                    "actual_start"
                ] = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

            if current_progress >= 100:

                activity_update[
                    "status"
                ] = "completed"

                if not activity.get(
                    "actual_finish"
                ):

                    activity_update[
                        "actual_finish"
                    ] = (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    )

            else:

                activity_update[
                    "status"
                ] = "in_progress"

    # ---------------------------------------------------------------
    # Progress itself can determine status
    # ---------------------------------------------------------------

    if current_progress >= 100:

        activity_update[
            "actual_progress"
        ] = 100

        activity_update[
            "status"
        ] = "completed"

        if not activity.get(
            "actual_start"
        ):

            activity_update[
                "actual_start"
            ] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

        if not activity.get(
            "actual_finish"
        ):

            activity_update[
                "actual_finish"
            ] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

    elif (
        current_progress > 0
        and activity_update.get(
            "status"
        )
        != "delayed"
    ):

        activity_update[
            "status"
        ] = "in_progress"

        if not activity.get(
            "actual_start"
        ):

            activity_update[
                "actual_start"
            ] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

    # ---------------------------------------------------------------
    # Persist activity updates
    # ---------------------------------------------------------------

    if activity_update:

        (
            supabase
            .table("activities")
            .update(
                activity_update
            )
            .eq(
                "id",
                activity_id,
            )
            .execute()
        )

        print(
            "[ACTIVITY UPDATE]",
            activity_id,
            activity_update,
        )

    # ---------------------------------------------------------------
    # Attach progress calculation to API response
    # ---------------------------------------------------------------

    if execution_event:

        execution_event[
            "physical_progress"
        ] = progress_result

    return execution_event


# -------------------------------------------------------------------
# Generate matches
# -------------------------------------------------------------------

@router.post(
    "/field-event/"
    "{field_event_id}"
)
def generate_activity_matches(
    field_event_id: str,
    current_user: dict = Depends(
        get_current_user
    ),
):

    event_response = (
        supabase
        .table("field_events")
        .select("*")
        .eq(
            "id",
            field_event_id,
        )
        .limit(1)
        .execute()
    )

    if not event_response.data:

        raise HTTPException(
            status_code=404,
            detail="Field event not found.",
        )

    event = (
        event_response.data[0]
    )

    project_id = (
        event["project_id"]
    )

    # ---------------------------------------------------------------
    # Existing matches
    # ---------------------------------------------------------------

    existing_response = (
        supabase
        .table("activity_matches")
        .select("*")
        .eq(
            "field_event_id",
            field_event_id,
        )
        .order(
            "confidence",
            desc=True,
        )
        .execute()
    )

    if existing_response.data:

        return {
            "field_event_id":
                field_event_id,

            "project_id":
                project_id,

            "source":
                "existing",

            "count":
                len(
                    existing_response.data
                ),

            "stored_matches":
                existing_response.data,
        }

    # ---------------------------------------------------------------
    # Extraction
    #
    # Extract exactly once for a new field event and persist the
    # normalized representation into field_events.extracted_data.
    # ---------------------------------------------------------------

    extracted = (
        get_or_create_stored_extraction(
            event
        )
    )

    print(
        "[EXTRACTION] Using structured event:",
        extracted.model_dump(),
    )

    # ---------------------------------------------------------------
    # Load schedule
    # ---------------------------------------------------------------

    activities = (
        get_all_project_activities(
            project_id
        )
    )

    # ---------------------------------------------------------------
    # Project Knowledge Memory
    # ---------------------------------------------------------------

    project_knowledge = (
        get_project_knowledge(
            project_id
        )
    )

    print(
        "[MATCHING] Activities searched:",
        len(activities),
    )

    print(
        "[MATCHING] Project memory loaded:",
        len(project_knowledge),
    )

    # ---------------------------------------------------------------
    # Semantic + Context + Memory reconciliation
    # ---------------------------------------------------------------

    ranked_matches = (
        rank_with_reconciliation(
            extracted=extracted,
            raw_text=event[
                "raw_text"
            ],
            activities=activities,
            top_k=5,
            project_knowledge=(
                project_knowledge
            ),
        )
    )

    # ---------------------------------------------------------------
    # Confidence Guardrail
    # ---------------------------------------------------------------

    guardrail = (
        evaluate_match_guardrail(
            ranked_matches
        )
    )

    print(
        "[MATCHING] Guardrail decision:",
        guardrail["decision"],
    )

    print(
        "[MATCHING] Top confidence:",
        guardrail[
            "top_confidence"
        ],
    )

    print(
        "[MATCHING] Margin:",
        guardrail["margin"],
    )

    # ---------------------------------------------------------------
    # Store candidate matches
    # ---------------------------------------------------------------

    rows_to_insert = []

    for (
        index,
        match,
    ) in enumerate(
        ranked_matches
    ):

        match_status = (
            "suggested"
        )

        if guardrail[
            "auto_verify"
        ]:

            if index == 0:

                match_status = (
                    "approved"
                )

            else:

                match_status = (
                    "rejected"
                )

        rows_to_insert.append(
            {
                "field_event_id":
                    field_event_id,

                "activity_id":
                    match[
                        "activity_id"
                    ],

                "confidence":
                    match[
                        "confidence"
                    ],

                "semantic_score":
                    match.get(
                        "semantic_score",
                        0,
                    ),

                "context_score":
                    match.get(
                        "context_score",
                        0,
                    ),

                "reason":
                    match.get(
                        "reason",
                        "activity candidate",
                    ),

                "status":
                    match_status,
            }
        )

    if not rows_to_insert:

        raise HTTPException(
            status_code=422,
            detail=(
                "No activity candidates "
                "could be generated."
            ),
        )

    insert_response = (
        supabase
        .table("activity_matches")
        .insert(
            rows_to_insert
        )
        .execute()
    )

    execution_event = None

    # ---------------------------------------------------------------
    # AUTO VERIFIED path
    # ---------------------------------------------------------------

    if (
        guardrail["auto_verify"]
        and insert_response.data
    ):

        approved_match = next(
            (
                row
                for row
                in insert_response.data
                if row.get(
                    "status"
                )
                == "approved"
            ),
            None,
        )

        if approved_match:

            execution_event = (
                create_execution_event_from_match(
                    event=event,
                    match=(
                        approved_match
                    ),
                )
            )

            (
                supabase
                .table("audit_logs")
                .insert(
                    {
                        "project_id":
                            project_id,

                        "user_id":
                            current_user[
                                "id"
                            ],

                        "action":
                            (
                                "activity_match_"
                                "auto_verified"
                            ),

                        "entity_type":
                            "activity_match",

                        "entity_id":
                            approved_match[
                                "id"
                            ],

                        "old_value":
                            None,

                        "new_value": {
                            "status":
                                "approved",

                            "activity_id":
                                approved_match[
                                    "activity_id"
                                ],

                            "execution_event_id":
                                (
                                    execution_event
                                    .get("id")
                                    if execution_event
                                    else None
                                ),

                            "physical_progress":
                                (
                                    execution_event
                                    .get(
                                        "physical_progress"
                                    )
                                    if execution_event
                                    else None
                                ),

                            "automation":
                                True,

                            "guardrail":
                                guardrail,
                        },
                    }
                )
                .execute()
            )

    # ---------------------------------------------------------------
    # Update field event
    # ---------------------------------------------------------------

    (
        supabase
        .table("field_events")
        .update(
            {
                "status":
                    "matched"
            }
        )
        .eq(
            "id",
            field_event_id,
        )
        .execute()
    )

    return {
        "field_event_id":
            field_event_id,

        "project_id":
            project_id,

        "matching_engine":
            (
                "semantic_context_"
                "reconciliation"
            ),

        "project_memory_count":
            len(
                project_knowledge
            ),

        "activities_searched":
            len(
                activities
            ),

        "semantic_candidates":
            min(
                10,
                len(
                    activities
                ),
            ),

        "extracted":
            extracted.model_dump(),

        "decision":
            guardrail[
                "decision"
            ],

        "guardrail":
            guardrail,

        "execution_event":
            execution_event,

        "count":
            len(
                ranked_matches
            ),

        "matches":
            ranked_matches,

        "stored_matches":
            (
                insert_response.data
                or []
            ),
    }


# -------------------------------------------------------------------
# Get matches for a field event
# -------------------------------------------------------------------

@router.get(
    "/field-event/"
    "{field_event_id}"
)
def get_activity_matches(
    field_event_id: str,
    current_user: dict = Depends(
        get_current_user
    ),
):

    match_response = (
        supabase
        .table("activity_matches")
        .select("*")
        .eq(
            "field_event_id",
            field_event_id,
        )
        .order(
            "confidence",
            desc=True,
        )
        .execute()
    )

    matches = (
        match_response.data
        or []
    )

    enriched = []

    for match in matches:

        activity_response = (
            supabase
            .table("activities")
            .select("*")
            .eq(
                "id",
                match[
                    "activity_id"
                ],
            )
            .limit(1)
            .execute()
        )

        activity = None

        if activity_response.data:

            activity = (
                activity_response
                .data[0]
            )

        enriched.append(
            {
                **match,
                "activity":
                    activity,
            }
        )

    return {
        "field_event_id":
            field_event_id,

        "count":
            len(
                enriched
            ),

        "matches":
            enriched,
    }


# -------------------------------------------------------------------
# Review Queue
# -------------------------------------------------------------------

@router.get(
    "/review-queue"
)
def get_review_queue(
    current_user: dict = Depends(
        require_reviewer
    ),
):

    match_response = (
        supabase
        .table("activity_matches")
        .select("*")
        .eq(
            "status",
            "suggested",
        )
        .order(
            "created_at",
            desc=False,
        )
        .execute()
    )

    suggested_matches = (
        match_response.data
        or []
    )

    grouped = {}

    for match in suggested_matches:

        field_event_id = (
            match[
                "field_event_id"
            ]
        )

        if (
            field_event_id
            not in grouped
        ):

            event_response = (
                supabase
                .table("field_events")
                .select("*")
                .eq(
                    "id",
                    field_event_id,
                )
                .limit(1)
                .execute()
            )

            event = None

            if event_response.data:

                event = (
                    event_response
                    .data[0]
                )

            grouped[
                field_event_id
            ] = {
                "field_event":
                    event,

                "matches":
                    [],
            }

        activity_response = (
            supabase
            .table("activities")
            .select("*")
            .eq(
                "id",
                match[
                    "activity_id"
                ],
            )
            .limit(1)
            .execute()
        )

        activity = None

        if activity_response.data:

            activity = (
                activity_response
                .data[0]
            )

        grouped[
            field_event_id
        ][
            "matches"
        ].append(
            {
                **match,
                "activity":
                    activity,
            }
        )

    return {
        "count":
            len(
                grouped
            ),

        "items":
            list(
                grouped.values()
            ),
    }


# -------------------------------------------------------------------
# Planner approves candidate
# -------------------------------------------------------------------

@router.post(
    "/{match_id}/approve"
)
def approve_match(
    match_id: str,
    current_user: dict = Depends(
        require_reviewer
    ),
):

    match_response = (
        supabase
        .table("activity_matches")
        .select("*")
        .eq(
            "id",
            match_id,
        )
        .limit(1)
        .execute()
    )

    if not match_response.data:

        raise HTTPException(
            status_code=404,
            detail="Match not found.",
        )

    match = (
        match_response.data[0]
    )

    field_event_id = (
        match[
            "field_event_id"
        ]
    )

    # ---------------------------------------------------------------
    # Get field event
    # ---------------------------------------------------------------

    event_response = (
        supabase
        .table("field_events")
        .select("*")
        .eq(
            "id",
            field_event_id,
        )
        .limit(1)
        .execute()
    )

    if not event_response.data:

        raise HTTPException(
            status_code=404,
            detail="Field event not found.",
        )

    event = (
        event_response.data[0]
    )

    # ---------------------------------------------------------------
    # Reject alternatives
    # ---------------------------------------------------------------

    (
        supabase
        .table("activity_matches")
        .update(
            {
                "status":
                    "rejected"
            }
        )
        .eq(
            "field_event_id",
            field_event_id,
        )
        .neq(
            "id",
            match_id,
        )
        .execute()
    )

    # ---------------------------------------------------------------
    # Approve selected candidate
    # ---------------------------------------------------------------

    approved_response = (
        supabase
        .table("activity_matches")
        .update(
            {
                "status":
                    "approved",

                "reviewed_by":
                    current_user[
                        "id"
                    ],

                "reviewed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
            }
        )
        .eq(
            "id",
            match_id,
        )
        .execute()
    )

    approved_match = (
        match
    )

    if approved_response.data:

        approved_match = (
            approved_response.data[0]
        )

    # ---------------------------------------------------------------
    # Execution Event + Physical Progress
    #
    # create_execution_event_from_match() now reuses the stored
    # extracted_data rather than asking Gemini to interpret the
    # original evidence again.
    # ---------------------------------------------------------------

    execution_event = (
        create_execution_event_from_match(
            event=event,
            match=approved_match,
        )
    )

    # ---------------------------------------------------------------
    # Learn Project Knowledge
    # ---------------------------------------------------------------

    learned_knowledge = (
        learn_from_planner_correction(
            event=event,
            approved_match=(
                approved_match
            ),
            current_user_id=(
                current_user["id"]
            ),
        )
    )

    print(
        "[PROJECT MEMORY] Learned entries:",
        len(
            learned_knowledge
        ),
    )

    # ---------------------------------------------------------------
    # Update field event
    # ---------------------------------------------------------------

    (
        supabase
        .table("field_events")
        .update(
            {
                "status":
                    "matched"
            }
        )
        .eq(
            "id",
            field_event_id,
        )
        .execute()
    )

    # ---------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------

    (
        supabase
        .table("audit_logs")
        .insert(
            {
                "project_id":
                    event[
                        "project_id"
                    ],

                "user_id":
                    current_user[
                        "id"
                    ],

                "action":
                    (
                        "activity_match_"
                        "approved"
                    ),

                "entity_type":
                    "activity_match",

                "entity_id":
                    match_id,

                "old_value": {
                    "status":
                        match.get(
                            "status"
                        )
                },

                "new_value": {
                    "status":
                        "approved",

                    "activity_id":
                        match[
                            "activity_id"
                        ],

                    "execution_event_id":
                        (
                            execution_event
                            .get("id")
                            if execution_event
                            else None
                        ),

                    "physical_progress":
                        (
                            execution_event
                            .get(
                                "physical_progress"
                            )
                            if execution_event
                            else None
                        ),

                    "learned_knowledge_ids":
                        [
                            item["id"]
                            for item
                            in learned_knowledge
                            if item.get(
                                "id"
                            )
                        ],
                },
            }
        )
        .execute()
    )

    return {
        "message":
            "Match approved.",

        "match":
            approved_match,

        "execution_event":
            execution_event,

        "physical_progress":
            (
                execution_event
                .get(
                    "physical_progress"
                )
                if execution_event
                else None
            ),

        "learned_knowledge":
            learned_knowledge,
    }


# -------------------------------------------------------------------
# Planner rejects candidate
# -------------------------------------------------------------------

@router.post(
    "/{match_id}/reject"
)
def reject_match(
    match_id: str,
    current_user: dict = Depends(
        require_reviewer
    ),
):

    match_response = (
        supabase
        .table("activity_matches")
        .select("*")
        .eq(
            "id",
            match_id,
        )
        .limit(1)
        .execute()
    )

    if not match_response.data:

        raise HTTPException(
            status_code=404,
            detail="Match not found.",
        )

    match = (
        match_response.data[0]
    )

    # ---------------------------------------------------------------
    # Reject
    # ---------------------------------------------------------------

    rejected_response = (
        supabase
        .table("activity_matches")
        .update(
            {
                "status":
                    "rejected",

                "reviewed_by":
                    current_user[
                        "id"
                    ],

                "reviewed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
            }
        )
        .eq(
            "id",
            match_id,
        )
        .execute()
    )

    # ---------------------------------------------------------------
    # Check whether any candidates remain
    # ---------------------------------------------------------------

    remaining_response = (
        supabase
        .table("activity_matches")
        .select("id")
        .eq(
            "field_event_id",
            match[
                "field_event_id"
            ],
        )
        .eq(
            "status",
            "suggested",
        )
        .execute()
    )

    if not remaining_response.data:

        (
            supabase
            .table("field_events")
            .update(
                {
                    "status":
                        "flagged"
                }
            )
            .eq(
                "id",
                match[
                    "field_event_id"
                ],
            )
            .execute()
        )

    # ---------------------------------------------------------------
    # Get project ID for audit
    # ---------------------------------------------------------------

    event_response = (
        supabase
        .table("field_events")
        .select("*")
        .eq(
            "id",
            match[
                "field_event_id"
            ],
        )
        .limit(1)
        .execute()
    )

    project_id = None

    if event_response.data:

        project_id = (
            event_response
            .data[0]
            .get(
                "project_id"
            )
        )

    # ---------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------

    (
        supabase
        .table("audit_logs")
        .insert(
            {
                "project_id":
                    project_id,

                "user_id":
                    current_user[
                        "id"
                    ],

                "action":
                    (
                        "activity_match_"
                        "rejected"
                    ),

                "entity_type":
                    "activity_match",

                "entity_id":
                    match_id,

                "old_value": {
                    "status":
                        match.get(
                            "status"
                        )
                },

                "new_value": {
                    "status":
                        "rejected"
                },
            }
        )
        .execute()
    )

    rejected_match = (
        match
    )

    if rejected_response.data:

        rejected_match = (
            rejected_response.data[0]
        )

    return {
        "message":
            "Match rejected.",

        "match":
            rejected_match,
    }