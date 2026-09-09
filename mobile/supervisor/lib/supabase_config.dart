// Supabase client configuration.
// Use the publishable/anon key only. Never use the service_role key here.
const supabaseUrl = 'https://ggqitbvqjwpyebijtsym.supabase.co';
const supabasePublishableKey = 'sb_publishable_I0NG0dNXLKq2mxqjh-lXSw_rK5UIb79';

bool get isSupabaseConfigured =>
    supabaseUrl.startsWith('https://') &&
    !supabaseUrl.contains('YOUR_PROJECT_REF') &&
    supabasePublishableKey != 'YOUR_PUBLISHABLE_OR_ANON_KEY' &&
    supabasePublishableKey.isNotEmpty;
