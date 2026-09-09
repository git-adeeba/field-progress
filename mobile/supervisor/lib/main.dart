import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'models.dart';
import 'supabase_config.dart';
import 'supabase_service.dart';

const primaryTeal = Color(0xFF006D77);
const darkTeal = Color(0xFF173B3D);
const accentGold = Color(0xFFFFC857);
const successGreen = Color(0xFF2A9D8F);
const dangerRed = Color(0xFFE76F51);
const scaffoldBackground = Color(0xFFF6F8F7);
const darkBackground = Color(0xFF0D2426);
const darkModeText = Color(0xFFB7D9E8);
AppController? activeApp;
SupabaseService? activeService;


Color themeSeed(String name) => primaryTeal;

Future<void> activateProject({
  required BuildContext context,
  required AppController app,
  required SupabaseService service,
  required ProjectInfo project,
  bool showConfirmation = false,
}) async {
  final previousProject = app.selectedProject;

  app.setSelectedProject(project);

  try {
    final activities = await service.fetchSchedules(
      project.id,
      projectName: project.name,
    );

    app.setActivities(activities);

    if (showConfirmation && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Active project changed to ${project.name}.'),
        ),
      );
    }
  } catch (error) {
    if (previousProject != null) {
      app.setSelectedProject(previousProject);
    }

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not load ${project.name}: $error'),
        ),
      );
    }
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SupabaseClient? client;
  if (isSupabaseConfigured) {
    await Supabase.initialize(
      url: supabaseUrl,
      publishableKey: supabasePublishableKey,
    );
    client = Supabase.instance.client;
  }
  final service = SupabaseService(client);
  runApp(Hub(service: service));
}

class Hub extends StatefulWidget {
  const Hub({required this.service, super.key});
  final SupabaseService service;
  @override
  State<Hub> createState() => _HubState();
}

class _HubState extends State<Hub> {
  final app = AppController();
  late bool restoringSession = widget.service.isConfigured;

  @override
  void initState() {
    super.initState();
    _restoreSession();
  }

  Future<void> _restoreSession() async {
    if (!widget.service.isConfigured) return;
    try {
      final profile = await widget.service.restoreSession();
      if (profile != null) app.setProfile(profile);
    } finally {
      if (mounted) setState(() => restoringSession = false);
    }
  }

  @override
  void dispose() {
    app.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: app,
    builder: (context, child) => MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'InSite',
      theme: ThemeData(
        useMaterial3: true,
        fontFamily: app.fontFamily,
        colorScheme: const ColorScheme.light(
          primary: primaryTeal,
          onPrimary: Colors.white,
          secondary: accentGold,
          onSecondary: darkTeal,
          surface: Colors.white,
          onSurface: darkTeal,
          error: dangerRed,
          onError: Colors.white,
        ),
        scaffoldBackgroundColor: scaffoldBackground,
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          labelStyle: const TextStyle(color: darkTeal),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: primaryTeal, width: 1.5),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(
              color: darkTeal.withValues(alpha: 0.18),
              width: 1.5,
            ),
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(
              color: darkTeal.withValues(alpha: 0.18),
              width: 1.5,
            ),
          ),
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
            side: BorderSide(
              color: darkTeal.withValues(alpha: 0.18),
              width: 1.5,
            ),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: primaryTeal,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            minimumSize: const Size.fromHeight(50),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: primaryTeal,
            side: const BorderSide(color: primaryTeal, width: 1.4),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            minimumSize: const Size.fromHeight(48),
          ),
        ),
        snackBarTheme: const SnackBarThemeData(
          backgroundColor: darkTeal,
          contentTextStyle: TextStyle(color: Colors.white),
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        fontFamily: app.fontFamily,
        brightness: Brightness.dark,
        colorScheme: const ColorScheme.dark(
          primary: primaryTeal,
          onPrimary: Colors.white,
          secondary: accentGold,
          onSecondary: darkTeal,
          surface: darkTeal,
          onSurface: darkModeText,
          error: dangerRed,
          onError: Colors.white,
        ),
        scaffoldBackgroundColor: darkBackground,
        appBarTheme: const AppBarTheme(
          backgroundColor: darkBackground,
          foregroundColor: Colors.white,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: darkTeal,
          labelStyle: const TextStyle(color: darkModeText),
          hintStyle: TextStyle(color: darkModeText.withValues(alpha: 0.7)),
          prefixIconColor: accentGold,
          suffixIconColor: accentGold,
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(14)),
            borderSide: BorderSide(color: Colors.white24, width: 1.5),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(14)),
            borderSide: BorderSide(color: accentGold, width: 1.5),
          ),
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(color: darkModeText),
          bodyMedium: TextStyle(color: darkModeText),
          bodySmall: TextStyle(color: darkModeText),
          titleMedium: TextStyle(color: darkModeText),
          titleLarge: TextStyle(color: darkModeText),
          headlineSmall: TextStyle(color: darkModeText),
          headlineMedium: TextStyle(color: darkModeText),
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
          color: darkTeal,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(14)),
            side: BorderSide(color: Colors.white24, width: 1.5),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: primaryTeal,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(10)),
            ),
            minimumSize: const Size.fromHeight(50),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: darkModeText,
            side: const BorderSide(color: darkModeText, width: 1.2),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            minimumSize: const Size.fromHeight(48),
          ),
        ),
        snackBarTheme: const SnackBarThemeData(
          backgroundColor: accentGold,
          contentTextStyle: TextStyle(color: darkTeal),
        ),
      ),
      themeMode: app.isDarkMode ? ThemeMode.dark : ThemeMode.light,
      home: restoringSession
          ? const StartupSplash()
          : app.isSignedIn
          ? Shell(app: app, service: widget.service)
          : Login(app: app, service: widget.service),
    ),
  );
}

class StartupSplash extends StatelessWidget {
  const StartupSplash({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0.75, end: 1),
        duration: const Duration(milliseconds: 700),
        curve: Curves.easeOutBack,
        builder: (context, scale, child) =>
            Transform.scale(scale: scale, child: child),
        child: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Brand(),
            SizedBox(height: 24),
            CircularProgressIndicator(color: primaryTeal),
          ],
        ),
      ),
    ),
  );
}

class Login extends StatefulWidget {
  const Login({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<Login> createState() => _LoginState();
}

class _LoginState extends State<Login> {
  final email = TextEditingController();
  final password = TextEditingController();
  bool busy = false;
  bool obscurePassword = true;
  @override
  void dispose() {
    email.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (!email.text.contains('@') || password.text.length < 6) {
      snack('Enter a valid email and a 6+ character password.');
      return;
    }
    setState(() => busy = true);
    try {
      widget.app.setProfile(
        await widget.service.signIn(email.text.trim(), password.text),
      );
    } catch (error) {
      snack(error.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void snack(String value) =>
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(value)));
  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 440),
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: 1),
            duration: const Duration(milliseconds: 550),
            curve: Curves.easeOutCubic,
            builder: (context, opacity, child) =>
                Opacity(opacity: opacity, child: child),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Brand(),
                const SizedBox(height: 52),
                Text(
                  'Welcome back',
                  style: Theme.of(context).textTheme.headlineMedium
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                const Text('Your site intelligence, in one clear view.'),
                const SizedBox(height: 28),
                TextField(
                  controller: email,
                  decoration: const InputDecoration(
                    labelText: 'Email address',
                    prefixIcon: Icon(Icons.mail_outline),
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: password,
                  obscureText: obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      tooltip: obscurePassword
                          ? 'Show password'
                          : 'Hide password',
                      onPressed: () =>
                          setState(() => obscurePassword = !obscurePassword),
                      icon: Icon(
                        obscurePassword
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 22),
                FilledButton(
                  onPressed: busy ? null : submit,
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(54),
                  ),
                  child: busy
                      ? const CircularProgressIndicator()
                      : const Text('Sign in'),
                ),
                Center(
                  child: TextButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) =>
                            Register(app: widget.app, service: widget.service),
                      ),
                    ),
                    child: const Text('New to InSite? Create account'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class Register extends StatefulWidget {
  const Register({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<Register> createState() => _RegisterState();
}

class _RegisterState extends State<Register> {
  final name = TextEditingController();
  final email = TextEditingController();
  final phone = TextEditingController();
  final password = TextEditingController();
  final department = TextEditingController();
  final project = TextEditingController();
  bool busy = false;
  bool obscurePassword = true;
  @override
  void dispose() {
    for (final field in [name, email, phone, password, department, project]) {
      field.dispose();
    }
    super.dispose();
  }

  Future<void> submit() async {
    final fields = [name, email, phone, password, department, project];
    if (fields.any((field) => field.text.trim().isEmpty) ||
        password.text.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Complete every field. Password must be 6+ characters.',
          ),
        ),
      );
      return;
    }
    setState(() => busy = true);
    try {
      widget.app.setProfile(
        await widget.service.register(
          email: email.text.trim(),
          password: password.text,
          fullName: name.text.trim(),
          phoneNumber: phone.text.trim(),
          department: department.text.trim(),
          projectId: project.text.trim(),
        ),
      );
      if (mounted) Navigator.pop(context);
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Create account')),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        TweenAnimationBuilder<double>(
          tween: Tween(begin: 0, end: 1),
          duration: const Duration(milliseconds: 550),
          curve: Curves.easeOutCubic,
          builder: (context, opacity, child) =>
              Opacity(opacity: opacity, child: child),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Set up your supervisor profile',
                style: Theme.of(context).textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 24),
              for (final item in {
                'Full name': name,
                'Email address': email,
                'Phone number': phone,
                'Password': password,
                'Department': department,
                'Project ID': project,
              }.entries) ...[
                TextField(
                  controller: item.value,
                  obscureText: item.key == 'Password' && obscurePassword,
                  keyboardType: item.key == 'Phone number'
                      ? TextInputType.phone
                      : null,
                  decoration: InputDecoration(
                    labelText: item.key,
                    suffixIcon: item.key == 'Password'
                        ? IconButton(
                            tooltip: obscurePassword
                                ? 'Show password'
                                : 'Hide password',
                            onPressed: () => setState(
                              () => obscurePassword = !obscurePassword,
                            ),
                            icon: Icon(
                              obscurePassword
                                  ? Icons.visibility_outlined
                                  : Icons.visibility_off_outlined,
                            ),
                          )
                        : null,
                  ),
                ),
                const SizedBox(height: 14),
              ],
              FilledButton(
                onPressed: busy ? null : submit,
                child: busy
                    ? const CircularProgressIndicator()
                    : const Text('Create profile'),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class Shell extends StatefulWidget {
  const Shell({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int tab = 0;
  @override
  void initState() {
    super.initState();
    activeApp = widget.app;
    activeService = widget.service;
    _loadSchedules();
  }

  Future<void> _loadSchedules() async {
    final profile = widget.app.profile;
    if (profile == null) return;
    try {
      final projects = await widget.service.fetchProjects();
      if (!mounted) return;
      widget.app.setProjects(projects);

      if (projects.isEmpty) {
        widget.app.setActivities([]);
        return;
      }

      ProjectInfo? selected;
      for (final project in projects) {
        if (project.id == profile.projectId) {
          selected = project;
          break;
        }
      }
      selected ??= projects.first;

      await activateProject(
        context: context,
        app: widget.app,
        service: widget.service,
        project: selected,
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not load ONFIELD data: $error')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      Dashboard(app: widget.app, service: widget.service),
      Import(
        app: widget.app,
        service: widget.service,
        onReport: () => setState(() => tab = 4),
      ),
      MessengerPage(app: widget.app, service: widget.service),
      ActivityPage(app: widget.app, service: widget.service),
      Reports(app: widget.app, service: widget.service),
      Profile(app: widget.app, service: widget.service),
      SettingsPage(app: widget.app),
      NotificationsPage(app: widget.app),
      BudgetPage(app: widget.app),
      InventoryPage(app: widget.app),
      HelpPage(app: widget.app),
      RateUsPage(app: widget.app),
    ];
    return Scaffold(
      endDrawer: AppMenu(
        app: widget.app,
        service: widget.service,
        onNavigate: (value) => setState(() => tab = value),
      ),
      body: SafeArea(
        child: IndexedStack(index: tab, children: pages),
      ),
      bottomNavigationBar: NavigationBar(
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        selectedIndex: tab < 5 ? tab : 0,
        onDestinationSelected: (value) => setState(() => tab = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.upload_file_outlined),
            label: 'Import',
          ),
          NavigationDestination(
            icon: Icon(Icons.forum_outlined),
            label: 'Messenger',
          ),
          NavigationDestination(
            icon: Icon(Icons.trending_up),
            label: 'Progress',
          ),
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            label: 'Report',
          ),
        ],
      ),
    );
  }
}

class Dashboard extends StatelessWidget {
  const Dashboard({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  Widget build(BuildContext context) {
    final completion = app.activities.isEmpty
        ? 0
        : (app.activities.fold<double>(
                  0,
                  (sum, item) => sum + item.actualProgress,
                ) /
                app.activities.length)
            .round();
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning'
        : hour < 18
        ? 'Good afternoon'
        : 'Good evening';
    return Frame(
      title: '$greeting, ${app.profile!.fullName.split(' ').first}',
      subtitle: 'Here is the pulse of ${app.selectedProject?.name ?? 'your project'}.',
      children: [
        const Label('PROJECT'),
        if (app.projects.isNotEmpty)
          DropdownButtonFormField<String>(
            value: app.selectedProject?.id,
            decoration: const InputDecoration(
              labelText: 'Active project',
              prefixIcon: Icon(Icons.business_outlined),
            ),
            items: app.projects
                .map(
                  (project) => DropdownMenuItem<String>(
                    value: project.id,
                    child: Text(project.name),
                  ),
                )
                .toList(),
            onChanged: (projectId) async {
              if (projectId == null) return;

              ProjectInfo? project;
              for (final item in app.projects) {
                if (item.id == projectId) {
                  project = item;
                  break;
                }
              }

              if (project == null) return;

              await activateProject(
                context: context,
                app: app,
                service: service,
                project: project,
                showConfirmation: true,
              );
            },
          ),
        const SizedBox(height: 22),
        const Label('SITE PULSE'),
        Row(
          children: [
            Expanded(
              child: Stat(
                label: 'Completion',
                value: '$completion%',
                icon: Icons.trending_up,
                color: successGreen,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Stat(
                label: 'Tracked activities',
                value: '${app.activities.length}',
                icon: Icons.event_note,
                color: accentGold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        const Label('TODAY ON SITE'),
        if (app.activities.isEmpty)
          const Empty(
            icon: Icons.calendar_month_outlined,
            title: 'No scheduled activities',
            detail: 'Add activities in the schedule workflow to see them here.',
          )
        else
          for (final item in app.activities.take(5)) ActivityCard(item: item),
        const SizedBox(height: 24),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: darkTeal,
            borderRadius: BorderRadius.circular(18),
          ),
          child: const Row(
            children: [
              Icon(Icons.auto_awesome, color: accentGold),
              SizedBox(width: 14),
              Expanded(
                child: Text(
                  'AI field assistant\nUpload today\'s log to surface schedule risks.',
                  style: TextStyle(color: Colors.white, height: 1.5),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class MessengerPage extends StatefulWidget {
  const MessengerPage({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<MessengerPage> createState() => _MessengerPageState();
}

class _MessengerPageState extends State<MessengerPage> {
  final message = TextEditingController();
  final messagesByProject = <String, List<String>>{};
  @override
  void dispose() {
    message.dispose();
    super.dispose();
  }

  List<String> _messagesForActiveProject() {
    final projectId = widget.app.selectedProject?.id ?? '';
    return messagesByProject.putIfAbsent(projectId, () => <String>[]);
  }

  void send() {
    final value = message.text.trim();
    if (value.isEmpty) return;

    final project = widget.app.selectedProject;
    if (project == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select a project first.')),
      );
      return;
    }

    setState(() {
      _messagesForActiveProject().add(value);
      message.clear();
    });
  }

  Future<void> attach() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      withData: true,
    );
    if (result == null || !mounted) return;
    final file = result.files.single;
    try {
      final project = widget.app.selectedProject;
      if (project == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Select a project first.')),
          );
        }
        return;
      }

      await widget.service.uploadDocument(file, widget.app.profile!.id);
      if (mounted) {
        setState(
          () => _messagesForActiveProject().add(
            'Attached file for ${project.name}: ${file.name}',
          ),
        );
      }
    } catch (error) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not attach file: $error')),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final project = widget.app.selectedProject;
    final messages = _messagesForActiveProject();

    return Frame(
      title: 'Messenger',
      subtitle: project == null
          ? 'Select a project to start a project conversation'
          : '${project.name} · Planner ↔ Supervisor',
      children: [
        const SizedBox(height: 18),
        if (messages.isEmpty)
        const Empty(
          icon: Icons.forum_outlined,
          title: 'Start a conversation',
          detail: 'Send an update to the planner.',
        ),
      for (final item in messages)
        Card(
          child: ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('You'),
            subtitle: Text(item),
          ),
        ),
      const SizedBox(height: 12),
      Row(
        children: [
          IconButton(
            tooltip: 'Attach file',
            onPressed: attach,
            icon: const Icon(Icons.add_circle_outline),
          ),
          Expanded(
            child: TextField(
              controller: message,
              onSubmitted: (_) => send(),
              decoration: const InputDecoration(hintText: 'Write a message'),
            ),
          ),
          IconButton(
            tooltip: 'Send message',
            onPressed: send,
            icon: const Icon(Icons.send),
          ),
        ],
      ),
      ],
    );
  }
}

class Schedule extends StatefulWidget {
  const Schedule({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<Schedule> createState() => _ScheduleState();
}

class _ScheduleState extends State<Schedule> {
  Future<void> add() async {
    final value = await showModalBottomSheet<ScheduleActivity>(
      context: context,
      isScrollControlled: true,
      builder: (_) => ActivityEditor(profile: widget.app.profile!),
    );
    if (value == null) return;
    await widget.service.saveSchedule(value, widget.app.profile!.id);
    widget.app.setActivities([...widget.app.activities, value]);
  }

  @override
  Widget build(BuildContext context) => Frame(
    title: 'Project schedule',
    subtitle: '${widget.app.selectedProject?.name ?? 'Select a project'} · Live plan',
    children: [
      Row(
        children: [
          Expanded(
            child: Stat(
              label: 'Planned today',
              value: '${widget.app.activities.length}',
              icon: Icons.event_available,
              color: primaryTeal,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Stat(
              label: 'On track',
              value:
                  '${widget.app.activities.where((item) => !item.isDelayed).length}',
              icon: Icons.check_circle_outline,
              color: successGreen,
            ),
          ),
        ],
      ),
      const SizedBox(height: 24),
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Label('ACTIVITY BOARD'),
          TextButton.icon(
            onPressed: add,
            icon: const Icon(Icons.add),
            label: const Text('Add activity'),
          ),
        ],
      ),
      if (widget.app.activities.isEmpty)
        const Empty(
          icon: Icons.calendar_month_outlined,
          title: 'No activities yet',
          detail: 'Add the first activity to start tracking your plan.',
        ),
      for (final item in widget.app.activities) ActivityCard(item: item),
    ],
  );
}

class ActivityEditor extends StatefulWidget {
  const ActivityEditor({required this.profile, super.key});
  final SupervisorProfile profile;
  @override
  State<ActivityEditor> createState() => _ActivityEditorState();
}

class _ActivityEditorState extends State<ActivityEditor> {
  final project = TextEditingController();
  final discipline = TextEditingController();
  final activity = TextEditingController();
  DateTime scheduled = DateTime.now().add(const Duration(hours: 2));
  DateTime? start;
  DateTime? end;
  DateTime? actual;
  @override
  void dispose() {
    project.dispose();
    discipline.dispose();
    activity.dispose();
    super.dispose();
  }

  Future<void> pick(String field) async {
    final current = field == 'planned'
        ? scheduled
        : field == 'start'
        ? start
        : field == 'end'
        ? end
        : actual;
    final date = await showDatePicker(
      context: context,
      firstDate: DateTime(2024),
      lastDate: DateTime(2035),
      initialDate: current ?? DateTime.now(),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(current ?? DateTime.now()),
    );
    if (time == null) return;
    final value = DateTime(
      date.year,
      date.month,
      date.day,
      time.hour,
      time.minute,
    );
    setState(() {
      if (field == 'planned') scheduled = value;
      if (field == 'start') start = value;
      if (field == 'end') end = value;
      if (field == 'actual') actual = value;
    });
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.only(
      left: 20,
      right: 20,
      top: 20,
      bottom: MediaQuery.viewInsetsOf(context).bottom + 20,
    ),
    child: SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Add site activity',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 18),
          TextField(
            controller: project,
            decoration: const InputDecoration(labelText: 'Project name'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: discipline,
            decoration: const InputDecoration(labelText: 'Discipline'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: activity,
            decoration: const InputDecoration(labelText: 'Activity name'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => pick('planned'),
            icon: const Icon(Icons.schedule),
            label: Text('Planned time · ${dateText(scheduled)}'),
          ),
          OutlinedButton.icon(
            onPressed: () => pick('start'),
            icon: const Icon(Icons.play_circle_outline),
            label: Text(
              start == null
                  ? 'Add start time'
                  : 'Started · ${dateText(start!)}',
            ),
          ),
          OutlinedButton.icon(
            onPressed: () => pick('end'),
            icon: const Icon(Icons.stop_circle_outlined),
            label: Text(
              end == null ? 'Add end time' : 'Ended · ${dateText(end!)}',
            ),
          ),
          OutlinedButton.icon(
            onPressed: () => pick('actual'),
            icon: const Icon(Icons.fact_check_outlined),
            label: Text(
              actual == null
                  ? 'Add actual time'
                  : 'Actual · ${dateText(actual!)}',
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: () {
              if (activity.text.trim().isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Enter an activity name.')),
                );
                return;
              }
              Navigator.pop(
                context,
                ScheduleActivity(
                  projectId: widget.profile.projectId,
                  projectName: project.text,
                  discipline: discipline.text,
                  activityName: activity.text.trim(),
                  scheduledTime: scheduled,
                  startTime: start,
                  endTime: end,
                  actualTime: actual,
                  progressStage: end == null ? 'In progress' : 'Completed',
                  status: end == null ? 'Pending' : 'Complete',
                ),
              );
            },
            icon: const Icon(Icons.save_outlined),
            label: const Text('Save activity'),
          ),
        ],
      ),
    ),
  );
}

class Import extends StatefulWidget {
  const Import({
    required this.app,
    required this.service,
    required this.onReport,
    this.initialPrompt = '',
    super.key,
  });
  final AppController app;
  final SupabaseService service;
  final VoidCallback onReport;
  final String initialPrompt;
  @override
  State<Import> createState() => _ImportState();
}

class _ImportState extends State<Import> {
  PlatformFile? file;
  late final prompt = TextEditingController(text: widget.initialPrompt);
  final speech = SpeechToText();

  String inputMode = 'text';
  bool busy = false;
  bool listening = false;
  int step = 0;

  @override
  void dispose() {
    prompt.dispose();
    speech.stop();
    super.dispose();
  }

  Future<void> toggleVoice() async {
    if (listening) {
      await speech.stop();
      if (mounted) {
        setState(() => listening = false);
      }
      return;
    }

    final available = await speech.initialize(
      onStatus: (status) {
        if ((status == 'done' || status == 'notListening') && mounted) {
          setState(() => listening = false);
        }
      },
      onError: (error) {
        if (!mounted) return;
        setState(() => listening = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Voice input error: ${error.errorMsg}'),
          ),
        );
      },
    );

    if (!available || !mounted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Voice input is not available. Check microphone permission.',
            ),
          ),
        );
      }
      return;
    }

    setState(() {
      inputMode = 'text';
      listening = true;
    });

    await speech.listen(
      partialResults: true,
      onResult: (result) {
        if (!mounted) return;

        prompt.text = result.recognizedWords;
        prompt.selection = TextSelection.fromPosition(
          TextPosition(offset: prompt.text.length),
        );
      },
    );
  }

  Future<void> choose() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      withData: true,
      allowedExtensions: ['pdf', 'csv', 'xlsx', 'txt'],
    );

    if (result == null || !mounted) return;

    setState(() {
      file = result.files.single;
      inputMode = 'file';
    });
  }

  Future<void> generate() async {
    final project = widget.app.selectedProject;

    if (project == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Select an ONFIELD project first.'),
        ),
      );
      return;
    }

    if (inputMode == 'text' && prompt.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Type or speak a field update first.'),
        ),
      );
      return;
    }

    if (inputMode == 'file' && file == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Choose a site document first.'),
        ),
      );
      return;
    }

    if (listening) {
      await speech.stop();
      if (mounted) setState(() => listening = false);
    }

    setState(() {
      busy = true;
      step = 1;
    });

    try {
      if (mounted) setState(() => step = 2);

      final IngestionResult result;

      if (inputMode == 'text') {
        result = await widget.service.ingestTextFieldInput(
          projectId: project.id,
          text: prompt.text,
        );
      } else {
        result = await widget.service.ingestFieldInput(
          projectId: project.id,
          file: file!,
        );
      }

      if (!mounted) return;

      // If AUTO_VERIFY changed an activity immediately, refresh the phone
      // so the new actual progress is visible without switching projects.
      try {
        final activities = await widget.service.fetchSchedules(
          project.id,
          projectName: project.name,
        );
        widget.app.setActivities(activities);
      } catch (error) {
        debugPrint(
          'Activity refresh after ingestion failed: $error',
        );
      }

      final extractedLines = <String>[];

      for (final item in result.createdEvents) {
        final extracted = Map<String, dynamic>.from(
          item['extracted'] as Map? ?? const {},
        );
        final event = Map<String, dynamic>.from(
          item['field_event'] as Map? ?? const {},
        );

        final parts = <String>[
          if ((extracted['discipline']?.toString() ?? '').isNotEmpty)
            extracted['discipline'].toString(),
          if ((extracted['area']?.toString() ?? '').isNotEmpty)
            extracted['area'].toString(),
          if (extracted['quantity'] != null)
            '${extracted['quantity']} ${extracted['unit'] ?? ''}'.trim(),
        ];

        final raw = event['raw_text']?.toString().trim() ?? '';

        if (raw.isNotEmpty) {
          extractedLines.add(
            parts.isEmpty ? raw : '${parts.join(' · ')} — $raw',
          );
        }
      }

      final decisionSummary = <String>[];

      if (result.autoVerified > 0) {
        decisionSummary.add(
          '${result.autoVerified} auto-verified',
        );
      }

      if (result.reviewRequired > 0) {
        decisionSummary.add(
          '${result.reviewRequired} sent for review',
        );
      }

      if (result.matchingFailed > 0) {
        decisionSummary.add(
          '${result.matchingFailed} matching failed',
        );
      }

      final decisionText = decisionSummary.isEmpty
          ? 'Matching completed'
          : decisionSummary.join(' · ');

      widget.app.setReport(
        FieldReport(
          summary: result.parsedItems == 1
              ? '1 field update was submitted to ONFIELD. $decisionText.'
              : '${result.parsedItems} field updates were submitted to ONFIELD. $decisionText.',
          metrics: {
            'Project': project.name,
            'Updates': '${result.parsedItems}',
            'Auto verified': '${result.autoVerified}',
            'Needs review': '${result.reviewRequired}',
          },
          risks: extractedLines
              .take(4)
              .map(
                (line) => {
                  'label': line.length > 80
                      ? '${line.substring(0, 77)}...'
                      : line,
                  'level': 'Captured',
                },
              )
              .toList(),
          filePath: result.filename,
          prompt: inputMode == 'text' ? prompt.text.trim() : '',
          createdAt: DateTime.now(),
        ),
      );

      setState(() {
        busy = false;
        step = 3;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '${result.parsedItems} update${result.parsedItems == 1 ? '' : 's'} processed · $decisionText.',
          ),
        ),
      );

      widget.onReport();
    } catch (error) {
      if (!mounted) return;

      setState(() {
        busy = false;
        step = 0;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Field update failed: $error'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final project = widget.app.selectedProject;

    return Frame(
      title: 'Add field update',
      subtitle: project == null
          ? 'Select a project before sending field evidence.'
          : '${project.name} · Field evidence intake',
      children: [
        const Label('ACTIVE PROJECT'),
        ActiveProjectCard(
          app: widget.app,
          service: widget.service,
        ),
        const SizedBox(height: 22),
        const Label('UPDATE METHOD'),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment<String>(
              value: 'text',
              icon: Icon(Icons.keyboard_alt_outlined),
              label: Text('Type / Voice'),
            ),
            ButtonSegment<String>(
              value: 'file',
              icon: Icon(Icons.upload_file_outlined),
              label: Text('Upload File'),
            ),
          ],
          selected: {inputMode},
          onSelectionChanged: busy
              ? null
              : (selection) {
                  setState(() {
                    inputMode = selection.first;
                  });
                },
        ),
        const SizedBox(height: 18),
        if (inputMode == 'text') ...[
          const Label('FIELD UPDATE'),
          TextField(
            controller: prompt,
            minLines: 4,
            maxLines: 7,
            decoration: InputDecoration(
              hintText:
                  'Example: XER-006 Welding pipeline joints in Pipe Rack is 25% complete.',
              suffixIcon: IconButton(
                tooltip: listening ? 'Stop listening' : 'Speak field update',
                onPressed: busy ? null : toggleVoice,
                icon: Icon(
                  listening ? Icons.mic : Icons.mic_none,
                  color: listening ? dangerRed : null,
                ),
              ),
            ),
          ),
          if (listening) ...[
            const SizedBox(height: 8),
            const Row(
              children: [
                Icon(
                  Icons.graphic_eq,
                  size: 18,
                  color: primaryTeal,
                ),
                SizedBox(width: 6),
                Text(
                  'Listening… speak the site update',
                  style: TextStyle(
                    color: primaryTeal,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ],
        ] else ...[
          const Label('SITE DOCUMENT'),
          OutlinedButton.icon(
            onPressed: busy ? null : choose,
            icon: const Icon(Icons.upload_file),
            label: Text(
              file?.name ?? 'Choose PDF, CSV, XLSX or TXT',
            ),
          ),
          if (file != null) ...[
            const SizedBox(height: 10),
            Card(
              child: ListTile(
                leading: const Icon(
                  Icons.description_outlined,
                  color: primaryTeal,
                ),
                title: Text(file!.name),
                subtitle: Text(
                  '${file!.size} bytes · Ready to process',
                ),
                trailing: IconButton(
                  tooltip: 'Remove file',
                  onPressed: busy
                      ? null
                      : () {
                          setState(() => file = null);
                        },
                  icon: const Icon(Icons.close),
                ),
              ),
            ),
          ],
        ],
        if (busy)
          Process(
            label: inputMode == 'text'
                ? 'Extracting and matching typed field update'
                : 'Extracting and matching uploaded field updates',
            active: step >= 2,
          ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: busy ? null : generate,
          icon: Icon(
            inputMode == 'text'
                ? Icons.send_outlined
                : Icons.auto_awesome,
          ),
          label: Text(
            busy
                ? 'Processing…'
                : inputMode == 'text'
                    ? 'Submit field update'
                    : 'Process uploaded file',
          ),
        ),
        const SizedBox(height: 8),
        Text(
          inputMode == 'text'
              ? 'Voice is converted to text on the phone, then the same ONFIELD extraction → matching → auto-verify/review pipeline is used.'
              : 'Uploaded files use the existing multi-format ONFIELD ingestion pipeline.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}


class ImportPromptDialog extends StatefulWidget {
  const ImportPromptDialog({super.key});
  @override
  State<ImportPromptDialog> createState() => _ImportPromptDialogState();
}

class _ImportPromptDialogState extends State<ImportPromptDialog> {
  final prompt = TextEditingController();
  final speech = SpeechToText();
  bool listening = false;

  @override
  void dispose() {
    prompt.dispose();
    speech.stop();
    super.dispose();
  }

  Future<void> toggleVoice() async {
    if (listening) {
      await speech.stop();
      if (mounted) setState(() => listening = false);
      return;
    }
    final available = await speech.initialize(
      onStatus: (status) {
        if (status == 'done' && mounted) setState(() => listening = false);
      },
    );
    if (!available || !mounted) return;
    setState(() => listening = true);
    await speech.listen(
      onResult: (result) {
        if (mounted) {
          prompt.text = result.recognizedWords;
          prompt.selection = TextSelection.fromPosition(
            TextPosition(offset: prompt.text.length),
          );
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Add field update'),
    content: TextField(
      controller: prompt,
      maxLines: 4,
      autofocus: true,
      decoration: InputDecoration(
        hintText: 'Type or speak the field update',
        suffixIcon: IconButton(
          tooltip: 'Voice input',
          onPressed: toggleVoice,
          icon: Icon(listening ? Icons.mic : Icons.mic_none),
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      FilledButton.icon(
        onPressed: () {
          final value = prompt.text.trim();
          Navigator.pop(context, value);
        },
        icon: const Icon(Icons.upload_file),
        label: const Text('Continue'),
      ),
    ],
  );
}

class Reports extends StatelessWidget {
  const Reports({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  Widget build(BuildContext context) {
    final project = app.selectedProject;
    final storedReport = app.latestReport;
    final reportBelongsToActiveProject =
        storedReport != null &&
        project != null &&
        storedReport.metrics['Project'] == project.name;
    final report = reportBelongsToActiveProject ? storedReport : null;

    return Frame(
      title: 'AI field report',
      subtitle: project == null
          ? 'Select a project to view its latest report'
          : report == null
              ? '${project.name} · No report generated yet'
              : '${project.name} · Generated from ${report.filePath}',
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: darkTeal,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'EXECUTIVE SUMMARY',
                style: TextStyle(
                  color: accentGold,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                report?.summary ??
                    'Upload a field log to generate your first AI brief.',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Label('KEY METRICS'),
        if (report != null)
          Row(
            children: [
              for (final item in report.metrics.entries.take(2))
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(right: 10),
                    child: Stat(
                      label: item.key,
                      value: item.value,
                      icon: Icons.insights_outlined,
                      color: primaryTeal,
                    ),
                  ),
                ),
            ],
          ),
        const SizedBox(height: 22),
        const Label('RISK ASSESSMENT'),
        if (report == null || report.risks.isEmpty)
          const Text('Risks will appear here after analysis.')
        else
          for (final risk in report.risks)
            Risk(label: risk['label']!, level: risk['level']!),
        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: report == null
                    ? null
                    : () => Clipboard.setData(
                        ClipboardData(text: report.summary),
                      ),
                icon: const Icon(Icons.copy),
                label: const Text('Copy'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: FilledButton.icon(
                onPressed: report == null
                    ? null
                    : () async {
                        final project = app.selectedProject;
                        if (project == null) return;

                        await service.saveReport(
                          report,
                          app.profile!.id,
                          project.id,
                        );
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Report saved to Supabase.'),
                          ),
                        );
                      },
                icon: const Icon(Icons.save_outlined),
                label: const Text('Save'),
              ),
            ),
            const SizedBox(width: 10),
            IconButton(
              onPressed: report == null
                  ? null
                  : () => SharePlus.instance.share(
                      ShareParams(text: report.summary),
                    ),
              icon: const Icon(Icons.ios_share),
            ),
          ],
        ),
      ],
    );
  }
}

class Profile extends StatelessWidget {
  const Profile({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  Widget build(BuildContext context) {
    final profile = app.profile!;
    return Frame(
      title: 'Profile',
      subtitle: 'Your operating preferences',
      children: [
        Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(12),
            leading: CircleAvatar(
              backgroundColor: accentGold,
              child: Text(profile.fullName[0]),
            ),
            title: Text(
              profile.fullName,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              '${profile.email}\n${profile.phoneNumber}\n${profile.department} · Active project: ${app.selectedProject?.name ?? 'Not selected'}',
            ),
            trailing: IconButton(
              onPressed: () => showDialog(
                context: context,
                builder: (_) => EditProfile(app: app, service: service),
              ),
              icon: const Icon(Icons.edit_outlined),
            ),
          ),
        ),
        const SizedBox(height: 24),
        const Label('ACTIVITY'),
        Row(
          children: [
            Expanded(
              child: Stat(
                label: 'Reports',
                value: app.latestReport == null ? '0' : '1',
                icon: Icons.description_outlined,
                color: primaryTeal,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Stat(
                label: 'Activities',
                value: '${app.activities.length}',
                icon: Icons.task_alt,
                color: accentGold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        const Label('PREFERENCES'),
        Card(
          child: Column(
            children: [
              SwitchListTile(
                title: const Text('Dark mode preview'),
                value: app.isDarkMode,
                onChanged: app.setDarkMode,
              ),
              const Divider(height: 1),
              SwitchListTile(
                title: const Text('Offline sync'),
                value: app.offlineSync,
                onChanged: app.setOfflineSync,
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        OutlinedButton.icon(
          onPressed: () async {
            await service.signOut();
            app.signOut();
          },
          icon: const Icon(Icons.logout),
          label: const Text('Sign out'),
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.redAccent,
            minimumSize: const Size.fromHeight(50),
          ),
        ),
      ],
    );
  }
}

class EditProfile extends StatefulWidget {
  const EditProfile({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<EditProfile> createState() => _EditProfileState();
}

class _EditProfileState extends State<EditProfile> {
  late final name = TextEditingController(text: widget.app.profile!.fullName);
  late final phone = TextEditingController(
    text: widget.app.profile!.phoneNumber,
  );
  late final department = TextEditingController(
    text: widget.app.profile!.department,
  );
  late final project = TextEditingController(
    text: widget.app.profile!.projectId,
  );
  @override
  void dispose() {
    name.dispose();
    phone.dispose();
    department.dispose();
    project.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Edit profile'),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        TextField(
          controller: name,
          decoration: const InputDecoration(labelText: 'Full name'),
        ),
        TextField(
          controller: phone,
          keyboardType: TextInputType.phone,
          decoration: const InputDecoration(labelText: 'Phone number'),
        ),
        TextField(
          controller: department,
          decoration: const InputDecoration(labelText: 'Department'),
        ),
        TextField(
          controller: project,
          decoration: const InputDecoration(labelText: 'Project ID'),
        ),
      ],
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      FilledButton(
        onPressed: () async {
          final updated = widget.app.profile!.copyWith(
            fullName: name.text,
            phoneNumber: phone.text,
            department: department.text,
            projectId: project.text,
          );
          await widget.service.updateProfile(updated);
          if (!context.mounted) return;
          widget.app.updateProfile(updated);
          Navigator.pop(context);
        },
        child: const Text('Save'),
      ),
    ],
  );
}

class SettingsPage extends StatelessWidget {
  const SettingsPage({required this.app, super.key});
  final AppController app;
  @override
  Widget build(BuildContext context) => Frame(
    title: 'Settings',
    subtitle: 'Manage your workspace preferences',
    children: [
      Card(
        child: Column(
          children: [
            SwitchListTile(
              title: const Text('Dark mode'),
              value: app.isDarkMode,
              onChanged: app.setDarkMode,
            ),
            const Divider(height: 1),
            SwitchListTile(
              title: const Text('Offline sync'),
              value: app.offlineSync,
              onChanged: app.setOfflineSync,
            ),
            const Divider(height: 1),
            DropdownButtonFormField<String>(
              initialValue: app.location,
              decoration: const InputDecoration(labelText: 'Location'),
              items: const [
                DropdownMenuItem(
                  value: 'North Campus',
                  child: Text('North Campus'),
                ),
                DropdownMenuItem(
                  value: 'South Campus',
                  child: Text('South Campus'),
                ),
                DropdownMenuItem(value: 'Remote', child: Text('Remote')),
              ],
              onChanged: (value) {
                if (value != null) app.setLocation(value);
              },
            ),
            DropdownButtonFormField<String>(
              initialValue: app.language,
              decoration: const InputDecoration(labelText: 'Language'),
              items: const [
                DropdownMenuItem(value: 'English', child: Text('English')),
                DropdownMenuItem(value: 'Hindi', child: Text('Hindi')),
                DropdownMenuItem(value: 'Marathi', child: Text('Marathi')),
              ],
              onChanged: (value) {
                if (value != null) app.setLanguage(value);
              },
            ),
          ],
        ),
      ),
    ],
  );
}

class NotificationsPage extends StatelessWidget {
  const NotificationsPage({required this.app, super.key});
  final AppController app;
  @override
  Widget build(BuildContext context) => Frame(
    title: 'Notifications',
    subtitle: 'Choose which site updates reach you',
    children: [
      Card(
        child: Column(
          children: [
            SwitchListTile(
              title: const Text('All notifications'),
              value: app.notificationsEnabled,
              onChanged: app.setNotificationsEnabled,
            ),
            const Divider(height: 1),
            SwitchListTile(
              title: const Text('Schedule reminders'),
              value: app.scheduleNotifications,
              onChanged: app.setScheduleNotifications,
            ),
            SwitchListTile(
              title: const Text('Risk alerts'),
              value: app.riskNotifications,
              onChanged: app.setRiskNotifications,
            ),
          ],
        ),
      ),
      const SizedBox(height: 18),
      const Empty(
        icon: Icons.notifications_none,
        title: 'No new notifications',
        detail: 'Your latest site updates will appear here.',
      ),
    ],
  );
}

class ActivityPage extends StatefulWidget {
  const ActivityPage({required this.app, required this.service, super.key});
  final AppController app;
  final SupabaseService service;
  @override
  State<ActivityPage> createState() => _ActivityPageState();
}

class _ActivityPageState extends State<ActivityPage> {
  Future<void> addActivity() async {
    final activity = await showModalBottomSheet<ScheduleActivity>(
      context: context,
      isScrollControlled: true,
      builder: (_) => ActivityEditor(profile: widget.app.profile!),
    );
    if (activity == null) return;
    try {
      if (widget.service.isConfigured) {
        await widget.service.saveSchedule(activity, widget.app.profile!.id);
      }
      widget.app.setActivities([...widget.app.activities, activity]);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not save activity: $error')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final activities = widget.app.activities;
    final delayed = activities.where((item) => item.isDelayed).length;
    final completion = activities.isEmpty
        ? 0
        : (activities.fold<double>(
                  0,
                  (sum, item) => sum + item.actualProgress,
                ) /
                activities.length)
            .round();

    return Frame(
      title: 'Progress',
      subtitle: '${widget.app.selectedProject?.name ?? 'Select a project'} · Activity completion and timing',
      children: [
        Row(
          children: [
            Expanded(
              child: Stat(
                label: 'Complete',
                value: '$completion%',
                icon: Icons.trending_up,
                color: successGreen,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Stat(
                label: 'Delayed',
                value: '$delayed',
                icon: Icons.warning_amber_outlined,
                color: dangerRed,
              ),
            ),
          ],
        ),
        const SizedBox(height: 22),
        const SizedBox(height: 4),
        const Label('ACTIVITIES'),
        if (activities.isEmpty)
          const Empty(
            icon: Icons.task_alt,
            title: 'No activities yet',
            detail: 'Add your first activity to begin tracking progress.',
          )
        else
          for (final activity in activities) ActivityCard(item: activity),
      ],
    );
  }
}

class BudgetPage extends StatelessWidget {
  const BudgetPage({required this.app, super.key});
  final AppController app;
  @override
  Widget build(BuildContext context) => Frame(
    title: 'Budget overview',
    subtitle: '${app.selectedProject?.name ?? 'Select a project'} · Cost snapshot',
    children: [
      Row(
        children: [
          Expanded(
            child: Stat(
              label: 'Committed',
              value: '68%',
              icon: Icons.account_balance_wallet_outlined,
              color: primaryTeal,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Stat(
              label: 'Remaining',
              value: '32%',
              icon: Icons.savings_outlined,
              color: accentGold,
            ),
          ),
        ],
      ),
      const SizedBox(height: 22),
      const Empty(
        icon: Icons.receipt_long_outlined,
        title: 'Budget details coming soon',
        detail: 'Connect your cost data to track commitments and forecasts.',
      ),
    ],
  );
}

class InventoryPage extends StatelessWidget {
  const InventoryPage({required this.app, super.key});
  final AppController app;
  @override
  Widget build(BuildContext context) => Frame(
    title: 'Inventory',
    subtitle: '${app.selectedProject?.name ?? 'Select a project'} · Materials and equipment',
    children: [
      Row(
        children: [
          Expanded(
            child: Stat(
              label: 'Tracked items',
              value: '24',
              icon: Icons.inventory_2_outlined,
              color: primaryTeal,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Stat(
              label: 'Low stock',
              value: '03',
              icon: Icons.warning_amber,
              color: accentGold,
            ),
          ),
        ],
      ),
      const SizedBox(height: 22),
      const Empty(
        icon: Icons.inventory_outlined,
        title: 'Inventory is ready',
        detail: 'Add materials and equipment to track stock on site.',
      ),
    ],
  );
}

class HelpPage extends StatelessWidget {
  const HelpPage({required this.app, super.key});
  final AppController app;
  @override
  Widget build(BuildContext context) => Frame(
    title: 'Help',
    subtitle: 'Get answers while you are on site',
    children: [
      Card(
        child: Column(
          children: const [
            ExpansionTile(
              title: Text('How do I import a site log?'),
              children: [
                Padding(
                  padding: EdgeInsets.all(16),
                  child: Text(
                    'Use Import from the taskbar or the floating Import button, then choose your file.',
                  ),
                ),
              ],
            ),
            ExpansionTile(
              title: Text('How do I add a schedule activity?'),
              children: [
                Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Open Planner and tap Add activity.'),
                ),
              ],
            ),
            ExpansionTile(
              title: Text('Where are notifications managed?'),
              children: [
                Padding(
                  padding: EdgeInsets.all(16),
                  child: Text(
                    'Open the three-dot menu and choose Notification manager.',
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      const SizedBox(height: 18),
      OutlinedButton.icon(
        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Support request started.')),
        ),
        icon: const Icon(Icons.support_agent),
        label: const Text('Contact support'),
      ),
    ],
  );
}

class RateUsPage extends StatefulWidget {
  const RateUsPage({required this.app, super.key});
  final AppController app;
  @override
  State<RateUsPage> createState() => _RateUsPageState();
}

class _RateUsPageState extends State<RateUsPage> {
  int rating = 0;
  @override
  Widget build(BuildContext context) => Frame(
    title: 'Rate InSite',
    subtitle: 'Tell us how the field workflow feels',
    children: [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              const Text(
                'How would you rate InSite?',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var index = 1; index <= 5; index++)
                    IconButton(
                      onPressed: () => setState(() => rating = index),
                      icon: Icon(
                        index <= rating ? Icons.star : Icons.star_border,
                        color: accentGold,
                        size: 34,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: rating == 0
                    ? null
                    : () => ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Thanks for your feedback.'),
                        ),
                      ),
                child: const Text('Submit rating'),
              ),
            ],
          ),
        ),
      ),
    ],
  );
}

class Frame extends StatelessWidget {
  const Frame({
    required this.title,
    required this.subtitle,
    required this.children,
    super.key,
  });
  final String title, subtitle;
  final List<Widget> children;

  Future<void> openProjectSwitcher(BuildContext context) async {
    final app = activeApp;
    final service = activeService;

    if (app == null || service == null || app.projects.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No ONFIELD projects are available.')),
      );
      return;
    }

    final selected = await showModalBottomSheet<ProjectInfo>(
      context: context,
      useRootNavigator: true,
      builder: (sheetContext) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            const ListTile(
              leading: Icon(Icons.business_outlined),
              title: Text(
                'Switch active project',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
              subtitle: Text(
                'Dashboard, activities, imports and reports will use this project.',
              ),
            ),
            const Divider(),
            for (final project in app.projects)
              RadioListTile<String>(
                value: project.id,
                groupValue: app.selectedProject?.id,
                title: Text(project.name),
                subtitle: Text(project.id),
                onChanged: (_) => Navigator.pop(sheetContext, project),
              ),
          ],
        ),
      ),
    );

    if (selected == null || !context.mounted) return;

    await activateProject(
      context: context,
      app: app,
      service: service,
      project: selected,
      showConfirmation: true,
    );
  }

  Future<void> openImport(BuildContext context) async {
    final value = await showDialog<String>(
      context: context,
      useRootNavigator: true,
      builder: (_) => const ImportPromptDialog(),
    );
    if (!context.mounted || value == null) return;
    final app = activeApp;
    final service = activeService;
    if (app == null || service == null) return;
    await Navigator.of(context, rootNavigator: true).push(
      MaterialPageRoute(
        builder: (_) => Import(
          app: app,
          service: service,
          initialPrompt: value,
          onReport: () => Navigator.of(context).pop(),
        ),
      ),
    );
  }

  void openNotifications(BuildContext context) {
    final app = activeApp;
    if (app == null) return;
    showModalBottomSheet<void>(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const ListTile(
              leading: Icon(Icons.notifications_active_outlined),
              title: Text('Notifications'),
              subtitle: Text('Manage site updates and schedule alerts'),
            ),
            SwitchListTile(
              title: const Text('All notifications'),
              value: app.notificationsEnabled,
              onChanged: app.setNotificationsEnabled,
            ),
            ListTile(
              leading: const Icon(Icons.tune_outlined),
              title: const Text('Open notification manager'),
              onTap: () {
                Navigator.pop(sheetContext);
                Scaffold.of(context).openEndDrawer();
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => Stack(
    children: [
      CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            backgroundColor: Theme.of(context).scaffoldBackgroundColor,
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
            actions: [
              IconButton(
                tooltip: activeApp?.selectedProject == null
                    ? 'Select project'
                    : 'Project: ${activeApp!.selectedProject!.name}',
                onPressed: () => openProjectSwitcher(context),
                icon: const Icon(Icons.business_outlined),
              ),
              IconButton(
                tooltip: 'Notifications',
                onPressed: () => openNotifications(context),
                icon: const Icon(Icons.notifications_none_outlined),
              ),
              IconButton(
                tooltip: 'Open menu',
                onPressed: () => Scaffold.of(context).openEndDrawer(),
                icon: const Icon(Icons.more_vert),
              ),
            ],
          ),
          SliverPadding(
            padding: const EdgeInsets.all(20),
            sliver: SliverList(delegate: SliverChildListDelegate(children)),
          ),
        ],
      ),
      if (activeApp != null && activeService != null)
        Positioned(
          right: 18,
          bottom: 88,
          child: FloatingActionButton.extended(
            onPressed: () => openImport(context),
            icon: const Icon(Icons.upload_file),
            label: const Text('Import'),
          ),
        ),
    ],
  );
}

class AppMenu extends StatelessWidget {
  const AppMenu({
    required this.app,
    required this.service,
    required this.onNavigate,
    super.key,
  });
  final AppController app;
  final SupabaseService service;
  final ValueChanged<int> onNavigate;

  void go(BuildContext context, int tab) {
    Navigator.pop(context);
    onNavigate(tab);
  }

  @override
  Widget build(BuildContext context) => Drawer(
    child: SafeArea(
      child: ListView(
        padding: const EdgeInsets.symmetric(vertical: 12),
        children: [
          UserAccountsDrawerHeader(
            decoration: const BoxDecoration(color: darkTeal),
            accountName: Text(
              app.profile?.fullName ?? 'Supervisor',
              style: const TextStyle(
                fontWeight: FontWeight.w800,
                color: darkModeText,
              ),
            ),
            accountEmail: Text(
              app.profile?.email ?? '',
              style: const TextStyle(color: darkModeText),
            ),
            currentAccountPicture: CircleAvatar(
              backgroundColor: primaryTeal,
              radius: 32,
              child: Text(
                (app.profile?.fullName ?? 'S')[0],
                style: const TextStyle(fontSize: 24, color: Colors.white),
              ),
            ),
            onDetailsPressed: () => go(context, 5),
          ),
          ListTile(
            title: const Text(
              'InSite menu',
              style: TextStyle(fontWeight: FontWeight.w800),
            ),
            subtitle: Text(
              app.selectedProject == null
                  ? 'No active project'
                  : 'Active: ${app.selectedProject!.name}',
            ),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Profile'),
            onTap: () => go(context, 5),
          ),
          SwitchListTile(
            secondary: const Icon(Icons.notifications_outlined),
            title: const Text('Notifications'),
            value: app.notificationsEnabled,
            onChanged: app.setNotificationsEnabled,
          ),
          ListTile(
            leading: const Icon(Icons.notifications_active_outlined),
            title: const Text('Notification manager'),
            subtitle: Text(
              app.notificationsEnabled
                  ? 'Alerts are enabled'
                  : 'Alerts are muted',
            ),
            onTap: () => go(context, 7),
          ),
          ListTile(
            leading: const Icon(Icons.history),
            title: const Text('Your activity'),
            subtitle: Text('${app.activities.length} schedule activities'),
            onTap: () => go(context, 3),
          ),
          ListTile(
            leading: const Icon(Icons.account_balance_wallet_outlined),
            title: const Text('Budget overview'),
            subtitle: const Text('Budget tracking workspace'),
            onTap: () => go(context, 8),
          ),
          ListTile(
            leading: const Icon(Icons.inventory_2_outlined),
            title: const Text('Inventory'),
            subtitle: const Text('Materials and equipment'),
            onTap: () => go(context, 9),
          ),
          ListTile(
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Settings'),
            onTap: () => go(context, 6),
          ),
          ListTile(
            leading: const Icon(Icons.help_outline),
            title: const Text('Help'),
            onTap: () => go(context, 10),
          ),
          ListTile(
            leading: const Icon(Icons.star_outline),
            title: const Text('Rate us'),
            onTap: () => go(context, 11),
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.redAccent),
            title: const Text('Log out'),
            onTap: () async {
              await service.signOut();
              if (context.mounted) {
                Navigator.pop(context);
                app.signOut();
              }
            },
          ),
        ],
      ),
    ),
  );
}


class ActiveProjectCard extends StatelessWidget {
  const ActiveProjectCard({
    required this.app,
    required this.service,
    super.key,
  });

  final AppController app;
  final SupabaseService service;

  @override
  Widget build(BuildContext context) {
    final project = app.selectedProject;

    return Card(
      child: ListTile(
        leading: const CircleAvatar(
          backgroundColor: primaryTeal,
          foregroundColor: Colors.white,
          child: Icon(Icons.business_outlined),
        ),
        title: Text(
          project?.name ?? 'No project selected',
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        subtitle: Text(
          project == null
              ? 'Choose a project before continuing.'
              : 'All field updates on this screen will be linked to this project.',
        ),
        trailing: TextButton(
          onPressed: app.projects.isEmpty
              ? null
              : () async {
                  final selected = await showModalBottomSheet<ProjectInfo>(
                    context: context,
                    builder: (sheetContext) => SafeArea(
                      child: ListView(
                        shrinkWrap: true,
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                        children: [
                          const ListTile(
                            title: Text(
                              'Choose project',
                              style: TextStyle(fontWeight: FontWeight.w800),
                            ),
                          ),
                          for (final item in app.projects)
                            RadioListTile<String>(
                              value: item.id,
                              groupValue: app.selectedProject?.id,
                              title: Text(item.name),
                              onChanged: (_) =>
                                  Navigator.pop(sheetContext, item),
                            ),
                        ],
                      ),
                    ),
                  );

                  if (selected == null || !context.mounted) return;

                  await activateProject(
                    context: context,
                    app: app,
                    service: service,
                    project: selected,
                    showConfirmation: true,
                  );
                },
          child: const Text('Change'),
        ),
      ),
    );
  }
}

class Brand extends StatelessWidget {
  const Brand({super.key});
  @override
  Widget build(BuildContext context) => const Row(
    children: [
      Icon(Icons.construction, color: primaryTeal, size: 38),
      SizedBox(width: 10),
      Text(
        'INSITE',
        style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.2),
      ),
    ],
  );
}

class Label extends StatelessWidget {
  const Label(this.text, {super.key});
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(
      text,
      style: const TextStyle(
        color: primaryTeal,
        fontWeight: FontWeight.bold,
        fontSize: 12,
        letterSpacing: 1.1,
      ),
    ),
  );
}

class Stat extends StatelessWidget {
  const Stat({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    super.key,
  });
  final String label, value;
  final IconData icon;
  final Color color;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color),
          const SizedBox(height: 10),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 24),
          ),
          Text(label, overflow: TextOverflow.ellipsis),
        ],
      ),
    ),
  );
}

class RowItem extends StatelessWidget {
  const RowItem({
    required this.time,
    required this.title,
    required this.detail,
    required this.status,
    super.key,
  });
  final String time, title, detail, status;
  @override
  Widget build(BuildContext context) => ListTile(
    leading: SizedBox(
      width: 46,
      child: Text(time, style: const TextStyle(fontWeight: FontWeight.bold)),
    ),
    title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
    subtitle: Text(detail),
    trailing: Text(
      status,
      style: const TextStyle(
        color: primaryTeal,
        fontWeight: FontWeight.bold,
        fontSize: 11,
      ),
    ),
  );
}

class ActivityCard extends StatelessWidget {
  const ActivityCard({required this.item, super.key});
  final ScheduleActivity item;
  @override
  Widget build(BuildContext context) {
    final normalizedStatus = item.status.toLowerCase();
    final statusColor = item.isDelayed
        ? dangerRed
        : item.actualProgress >= 100
            ? successGreen
            : item.actualProgress > 0
                ? accentGold
                : primaryTeal;
    final status = item.isDelayed
        ? 'Behind plan'
        : item.actualProgress >= 100
            ? 'Completed'
            : item.actualProgress > 0
                ? 'In progress'
                : normalizedStatus.replaceAll('_', ' ');
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        leading: Icon(
          item.isDelayed
              ? Icons.warning_amber_rounded
              : Icons.engineering_outlined,
          color: statusColor,
        ),
        title: Text(
          item.activityName,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(
          '${item.activityCode.isEmpty ? '' : '${item.activityCode} · '}${item.discipline.isEmpty ? 'General' : item.discipline}\nPlanned ${dateText(item.scheduledTime)}${item.plannedFinish == null ? '' : ' → ${dateText(item.plannedFinish!)}'}\nActual ${item.actualProgress.toStringAsFixed(item.actualProgress % 1 == 0 ? 0 : 1)}% · Planned ${item.plannedProgress.toStringAsFixed(item.plannedProgress % 1 == 0 ? 0 : 1)}%',
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              status,
              style: TextStyle(color: statusColor, fontWeight: FontWeight.bold),
            ),
            Text(
              item.varianceLabel,
              style: TextStyle(color: statusColor, fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}

class Process extends StatelessWidget {
  const Process({required this.label, required this.active, super.key});
  final String label;
  final bool active;
  @override
  Widget build(BuildContext context) => ListTile(
    leading: Icon(
      active ? Icons.check_circle : Icons.radio_button_unchecked,
      color: active ? successGreen : darkTeal.withValues(alpha: 0.45),
    ),
    title: Text(label),
  );
}

class Risk extends StatelessWidget {
  const Risk({required this.label, required this.level, super.key});
  final String label, level;
  @override
  Widget build(BuildContext context) {
    final color =
        level.toLowerCase() == 'critical' || level.toLowerCase() == 'high'
        ? dangerRed
        : level.toLowerCase() == 'medium'
        ? accentGold
        : successGreen;
    return Card(
      child: ListTile(
        leading: Icon(Icons.shield_outlined, color: color),
        title: Text(label),
        trailing: Chip(
          backgroundColor: color.withValues(alpha: 0.16),
          label: Text(
            level,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }
}

class Empty extends StatelessWidget {
  const Empty({
    required this.icon,
    required this.title,
    required this.detail,
    super.key,
  });
  final IconData icon;
  final String title, detail;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Center(
        child: Column(
          children: [
            Icon(icon, size: 42, color: primaryTeal),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
            Text(detail, textAlign: TextAlign.center),
          ],
        ),
      ),
    ),
  );
}

String dateText(DateTime value) =>
    '${value.day}/${value.month} ${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';