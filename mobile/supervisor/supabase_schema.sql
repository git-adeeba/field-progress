create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null,
  email text not null,
  phone_number text not null default '',
  department text not null,
  project_id text not null,
  updated_at timestamptz not null default now()
);

alter table public.profiles add column if not exists phone_number text not null default '';

create table if not exists public.schedules (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id text not null,
  project_name text not null,
  discipline text not null,
  activity_name text not null,
  scheduled_time timestamptz not null,
  start_time timestamptz,
  end_time timestamptz,
  actual_time timestamptz,
  progress_stage text not null default 'Planned',
  status text not null default 'Pending'
);

alter table public.schedules add column if not exists start_time timestamptz;
alter table public.schedules add column if not exists end_time timestamptz;

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id text not null,
  file_path text not null,
  user_prompt text,
  summary text not null,
  metrics_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.schedules enable row level security;
alter table public.reports enable row level security;

create policy "Users manage their profile" on public.profiles for all using (auth.uid() = id) with check (auth.uid() = id);
create policy "Users manage their schedules" on public.schedules for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users manage their reports" on public.reports for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

insert into storage.buckets (id, name, public) values ('site_documents', 'site_documents', false) on conflict (id) do nothing;
create policy "Users upload own documents" on storage.objects for insert to authenticated with check (bucket_id = 'site_documents' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "Users read own documents" on storage.objects for select to authenticated using (bucket_id = 'site_documents' and (storage.foldername(name))[1] = auth.uid()::text);
