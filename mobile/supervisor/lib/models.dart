import 'package:flutter/foundation.dart';

class ProjectInfo {
  const ProjectInfo({
    required this.id,
    required this.name,
    this.description,
    this.startDate,
    this.endDate,
    required this.status,
  });

  final String id;
  final String name;
  final String? description;
  final DateTime? startDate;
  final DateTime? endDate;
  final String status;

  factory ProjectInfo.fromMap(Map<String, dynamic> map) => ProjectInfo(
        id: map['id']?.toString() ?? '',
        name: map['name']?.toString() ?? 'Unnamed project',
        description: map['description']?.toString(),
        startDate: DateTime.tryParse(map['start_date']?.toString() ?? ''),
        endDate: DateTime.tryParse(map['end_date']?.toString() ?? ''),
        status: map['status']?.toString() ?? 'active',
      );
}

class SupervisorProfile {
  const SupervisorProfile({
    required this.id,
    required this.fullName,
    required this.email,
    required this.phoneNumber,
    required this.department,
    required this.projectId,
  });

  final String id;
  final String fullName;
  final String email;
  final String phoneNumber;
  final String department;
  final String projectId;

  SupervisorProfile copyWith({
    String? fullName,
    String? email,
    String? phoneNumber,
    String? department,
    String? projectId,
  }) =>
      SupervisorProfile(
        id: id,
        fullName: fullName ?? this.fullName,
        email: email ?? this.email,
        phoneNumber: phoneNumber ?? this.phoneNumber,
        department: department ?? this.department,
        projectId: projectId ?? this.projectId,
      );

  factory SupervisorProfile.fromMap(Map<String, dynamic> map) =>
      SupervisorProfile(
        id: map['id']?.toString() ?? '',
        fullName: map['full_name']?.toString() ?? 'Supervisor',
        email: map['email']?.toString() ?? '',
        phoneNumber: map['phone_number']?.toString() ?? '',
        department: map['department']?.toString() ?? 'Operations',
        projectId: map['project_id']?.toString() ?? '',
      );
}

class ScheduleActivity {
  const ScheduleActivity({
    this.id,
    required this.projectId,
    required this.projectName,
    required this.discipline,
    required this.activityName,
    required this.scheduledTime,
    this.startTime,
    this.endTime,
    this.actualTime,
    required this.progressStage,
    required this.status,
    this.activityCode = '',
    this.wbsLevel = '',
    this.area = '',
    this.plannedFinish,
    this.plannedProgress = 0,
    this.actualProgress = 0,
  });

  final String? id;
  final String projectId;
  final String projectName;
  final String discipline;
  final String activityName;
  final DateTime scheduledTime;
  final DateTime? startTime;
  final DateTime? endTime;
  final DateTime? actualTime;
  final String progressStage;
  final String status;
  final String activityCode;
  final String wbsLevel;
  final String area;
  final DateTime? plannedFinish;
  final double plannedProgress;
  final double actualProgress;

  factory ScheduleActivity.fromBackend(
    Map<String, dynamic> map, {
    required String projectName,
  }) {
    final actualProgress =
        double.tryParse(map['actual_progress']?.toString() ?? '0') ?? 0;
    final plannedProgress =
        double.tryParse(map['planned_progress']?.toString() ?? '0') ?? 0;

    return ScheduleActivity(
      id: map['id']?.toString(),
      projectId: map['project_id']?.toString() ?? '',
      projectName: projectName,
      discipline: map['discipline']?.toString() ?? '',
      activityName: map['activity_name']?.toString() ?? '',
      scheduledTime:
          DateTime.tryParse(map['planned_start']?.toString() ?? '') ??
              DateTime.now(),
      plannedFinish:
          DateTime.tryParse(map['planned_finish']?.toString() ?? ''),
      startTime: DateTime.tryParse(map['actual_start']?.toString() ?? ''),
      endTime: DateTime.tryParse(map['actual_finish']?.toString() ?? ''),
      actualTime: DateTime.tryParse(map['actual_finish']?.toString() ?? ''),
      progressStage: actualProgress >= 100
          ? 'Completed'
          : actualProgress > 0
              ? 'In progress'
              : 'Not started',
      status: map['status']?.toString() ?? 'not_started',
      activityCode: map['activity_code']?.toString() ?? '',
      wbsLevel: map['wbs_level']?.toString() ?? '',
      area: map['area']?.toString() ?? '',
      plannedProgress: plannedProgress,
      actualProgress: actualProgress,
    );
  }

  Map<String, dynamic> toMap(String userId) => {
        'user_id': userId,
        'project_id': projectId,
        'project_name': projectName,
        'discipline': discipline,
        'activity_name': activityName,
        'scheduled_time': scheduledTime.toIso8601String(),
        'start_time': startTime?.toIso8601String(),
        'end_time': endTime?.toIso8601String(),
        'actual_time': actualTime?.toIso8601String(),
        'progress_stage': progressStage,
        'status': status,
      };

  DateTime? get completionTime => endTime ?? actualTime;
  Duration? get variance => completionTime?.difference(scheduledTime);

  String get varianceLabel {
    if (actualProgress >= 100) return '100% complete';
    if (actualProgress > 0) {
      final digits = actualProgress % 1 == 0 ? 0 : 1;
      return '${actualProgress.toStringAsFixed(digits)}% complete';
    }
    return 'Not started';
  }

  bool get isDelayed =>
      plannedProgress > actualProgress && status.toLowerCase() != 'completed';
  bool get isOnTime => !isDelayed && actualProgress > 0;
}

class FieldReport {
  const FieldReport({
    this.id,
    required this.summary,
    required this.metrics,
    required this.risks,
    required this.filePath,
    required this.prompt,
    required this.createdAt,
  });

  final String? id;
  final String summary;
  final Map<String, String> metrics;
  final List<Map<String, String>> risks;
  final String filePath;
  final String prompt;
  final DateTime createdAt;

  Map<String, dynamic> toMap(String userId, String projectId) => {
        'user_id': userId,
        'project_id': projectId,
        'file_path': filePath,
        'user_prompt': prompt,
        'summary': summary,
        'metrics_json': metrics,
      };
}

class AppController extends ChangeNotifier {
  SupervisorProfile? profile;
  bool isDarkMode = false;
  bool offlineSync = true;
  bool notificationsEnabled = true;
  bool scheduleNotifications = true;
  bool riskNotifications = true;
  String location = 'North Campus';
  String fontFamily = 'Inter';
  String language = 'English';
  String themeName = 'Ocean';
  List<ProjectInfo> projects = [];
  ProjectInfo? selectedProject;
  List<ScheduleActivity> activities = [];
  FieldReport? latestReport;

  bool get isSignedIn => profile != null;

  void setProfile(SupervisorProfile value) {
    profile = value;
    notifyListeners();
  }

  void updateProfile(SupervisorProfile value) {
    profile = value;
    notifyListeners();
  }

  void setProjects(List<ProjectInfo> value) {
    projects = value;
    notifyListeners();
  }

  void setSelectedProject(ProjectInfo value) {
    selectedProject = value;
    if (profile != null) profile = profile!.copyWith(projectId: value.id);
    activities = [];
    notifyListeners();
  }

  void signOut() {
    profile = null;
    projects = [];
    selectedProject = null;
    activities = [];
    latestReport = null;
    notifyListeners();
  }

  void setDarkMode(bool value) { isDarkMode = value; notifyListeners(); }
  void setOfflineSync(bool value) { offlineSync = value; notifyListeners(); }
  void setNotificationsEnabled(bool value) { notificationsEnabled = value; notifyListeners(); }
  void setScheduleNotifications(bool value) { scheduleNotifications = value; notifyListeners(); }
  void setRiskNotifications(bool value) { riskNotifications = value; notifyListeners(); }
  void setLocation(String value) { location = value; notifyListeners(); }
  void setFontFamily(String value) { fontFamily = value; notifyListeners(); }
  void setLanguage(String value) { language = value; notifyListeners(); }
  void setTheme(String value) { themeName = value; notifyListeners(); }
  void setActivities(List<ScheduleActivity> value) { activities = value; notifyListeners(); }
  void setReport(FieldReport value) { latestReport = value; notifyListeners(); }
}
