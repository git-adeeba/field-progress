# InSite

## Connect Supabase

1. Create a Supabase project and open its SQL Editor.
2. Run the complete contents of [supabase_schema.sql](supabase_schema.sql).
3. Open [lib/supabase_config.dart](lib/supabase_config.dart) and replace `YOUR_PROJECT_REF` and `YOUR_PUBLISHABLE_OR_ANON_KEY` with your Supabase project values.

4. Start the app normally from VS Code or with:

```powershell
flutter run
```

Use the publishable/anon key only. Do not put a `service_role` key in the Flutter app.

Sign-in, registration, profiles, schedules, document uploads, and saved reports use Supabase. Existing auth sessions are restored when the app starts. The app reports a configuration error instead of silently discarding writes when the values are omitted.

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
