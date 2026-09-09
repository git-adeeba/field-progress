
import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';

import 'api_config.dart';
import 'models.dart';

class IngestionResult {
  const IngestionResult({
    required this.filename,
    required this.sourceType,
    required this.parsedItems,
    required this.createdEvents,
    required this.processedMatches,
    required this.autoVerified,
    required this.reviewRequired,
    required this.matchingFailed,
  });

  final String filename;
  final String sourceType;
  final int parsedItems;
  final List<Map<String, dynamic>> createdEvents;
  final int processedMatches;
  final int autoVerified;
  final int reviewRequired;
  final int matchingFailed;

  factory IngestionResult.fromJson(Map<String, dynamic> json) {
    final rawEvents = json['created_events'] as List<dynamic>? ?? const [];
    final matching =
        json['matching_summary'] as Map<String, dynamic>? ?? const {};

    return IngestionResult(
      filename: json['filename']?.toString() ?? '',
      sourceType: json['source_type']?.toString() ?? '',
      parsedItems: (json['parsed_items'] as num?)?.toInt() ?? rawEvents.length,
      createdEvents: rawEvents
          .map((item) => Map<String, dynamic>.from(item as Map))
          .toList(),
      processedMatches: (matching['processed'] as num?)?.toInt() ?? 0,
      autoVerified: (matching['auto_verified'] as num?)?.toInt() ?? 0,
      reviewRequired: (matching['review_required'] as num?)?.toInt() ?? 0,
      matchingFailed: (matching['failed'] as num?)?.toInt() ?? 0,
    );
  }
}

class SupabaseService {
  SupabaseService(this.client);

  final SupabaseClient? client;
  bool get isConfigured => client != null;

  void _requireConfigured() {
    if (client == null) {
      throw StateError('Supabase is not configured.');
    }
  }

  Map<String, String> get _apiHeaders {
    final token = client?.auth.currentSession?.accessToken;
    return {
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  Future<SupervisorProfile?> restoreSession() async {
    if (client == null) return null;
    final user = client!.auth.currentUser;
    if (user == null) return null;
    return fetchProfile(user.id, user.email ?? '');
  }

  Future<SupervisorProfile> signIn(String email, String password) async {
    _requireConfigured();
    final response = await client!.auth.signInWithPassword(
      email: email,
      password: password,
    );
    final user = response.user!;
    return fetchProfile(user.id, user.email ?? email);
  }

  Future<SupervisorProfile> register({
    required String email,
    required String password,
    required String fullName,
    required String phoneNumber,
    required String department,
    required String projectId,
  }) async {
    _requireConfigured();
    final response = await client!.auth.signUp(
      email: email,
      password: password,
      data: {
        'full_name': fullName,
        'phone_number': phoneNumber,
        'department': department,
        'project_id': projectId,
      },
    );
    final user = response.user!;
    await client!.from('profiles').upsert({
      'id': user.id,
      'full_name': fullName,
      'email': email,
      'phone_number': phoneNumber,
      'department': department,
      'project_id': projectId,
    });
    return SupervisorProfile(
      id: user.id,
      fullName: fullName,
      email: email,
      phoneNumber: phoneNumber,
      department: department,
      projectId: projectId,
    );
  }

  Future<SupervisorProfile> fetchProfile(String id, String email) async {
    final data =
        await client!.from('profiles').select().eq('id', id).maybeSingle();
    return SupervisorProfile.fromMap({
      ...data ?? {},
      'id': id,
      'email': data?['email'] ?? email,
    });
  }

  Future<void> updateProfile(SupervisorProfile profile) async {
    _requireConfigured();
    await client!
        .from('profiles')
        .update({
          'full_name': profile.fullName,
          'email': profile.email,
          'phone_number': profile.phoneNumber,
          'department': profile.department,
          'project_id': profile.projectId,
          'updated_at': DateTime.now().toIso8601String(),
        })
        .eq('id', profile.id);
  }

  Future<void> signOut() async {
    if (client != null) await client!.auth.signOut();
  }

  Future<List<ProjectInfo>> fetchProjects() async {
    final response = await http
        .get(Uri.parse('$backendBaseUrl/projects'), headers: _apiHeaders)
        .timeout(const Duration(seconds: 15));

    if (response.statusCode != 200) {
      throw Exception(
        'Projects API failed (${response.statusCode}): ${response.body}',
      );
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final rows = body['projects'] as List<dynamic>? ?? [];
    return rows
        .map((row) => ProjectInfo.fromMap(Map<String, dynamic>.from(row as Map)))
        .toList();
  }

  Future<List<ScheduleActivity>> fetchSchedules(
    String projectId, {
    String projectName = '',
  }) async {
    final response = await http
        .get(
          Uri.parse('$backendBaseUrl/projects/$projectId/activities'),
          headers: _apiHeaders,
        )
        .timeout(const Duration(seconds: 20));

    if (response.statusCode != 200) {
      throw Exception(
        'Activities API failed (${response.statusCode}): ${response.body}',
      );
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final rows = body['activities'] as List<dynamic>? ?? [];
    return rows
        .map(
          (row) => ScheduleActivity.fromBackend(
            Map<String, dynamic>.from(row as Map),
            projectName: projectName,
          ),
        )
        .toList();
  }

  Future<void> saveSchedule(ScheduleActivity activity, String userId) async {
    throw UnsupportedError(
      'Schedule editing is controlled from the planner website.',
    );
  }

  Future<IngestionResult> ingestFieldInput({
    required String projectId,
    required PlatformFile file,
  }) async {
    final token = client?.auth.currentSession?.accessToken;
    if (token == null || token.isEmpty) {
      throw StateError('Your login session is missing. Please sign in again.');
    }

    final bytes = file.bytes;
    if (bytes == null || bytes.isEmpty) {
      throw StateError(
        'Could not read the selected file. Choose the document again.',
      );
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$backendBaseUrl/ingestion/upload'),
    )
      ..headers['Authorization'] = 'Bearer $token'
      ..headers['Accept'] = 'application/json'
      ..fields['project_id'] = projectId
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: file.name,
        ),
      );

    final streamed = await request.send().timeout(const Duration(seconds: 90));
    final response = await http.Response.fromStream(streamed);

    Map<String, dynamic>? body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      body = null;
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body?['detail']?.toString() ?? response.body;
      throw Exception(
        detail.isEmpty
            ? 'Field ingestion failed (${response.statusCode}).'
            : detail,
      );
    }

    if (body == null) {
      throw Exception('The backend returned an invalid ingestion response.');
    }

    return IngestionResult.fromJson(body);
  }

  Future<IngestionResult> ingestTextFieldInput({
    required String projectId,
    required String text,
  }) async {
    final token = client?.auth.currentSession?.accessToken;
    if (token == null || token.isEmpty) {
      throw StateError('Your login session is missing. Please sign in again.');
    }

    final cleanText = text.trim();
    if (cleanText.isEmpty) {
      throw StateError('Type or speak a field update first.');
    }

    final response = await http
        .post(
          Uri.parse('$backendBaseUrl/ingestion/text'),
          headers: {
            ..._apiHeaders,
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            'project_id': projectId,
            'text': cleanText,
          }),
        )
        .timeout(const Duration(seconds: 90));

    Map<String, dynamic>? body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      body = null;
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body?['detail']?.toString() ?? response.body;
      throw Exception(
        detail.isEmpty
            ? 'Text ingestion failed (${response.statusCode}).'
            : detail,
      );
    }

    if (body == null) {
      throw Exception('The backend returned an invalid ingestion response.');
    }

    return IngestionResult.fromJson(body);
  }

  Future<String?> uploadDocument(PlatformFile file, String userId) async {
    _requireConfigured();
    if (file.bytes == null) return file.name;
    final path = '$userId/${DateTime.now().millisecondsSinceEpoch}_${file.name}';
    await client!.storage.from('site_documents').uploadBinary(path, file.bytes!);
    return path;
  }

  Future<void> saveReport(
    FieldReport report,
    String userId,
    String projectId,
  ) async {
    _requireConfigured();
    await client!.from('reports').insert(report.toMap(userId, projectId));
  }
}
