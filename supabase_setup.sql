-- ONYX Supabase Schema Setup
-- Run this in your Supabase SQL Editor to create the required tables.

create table if not exists conversations (
  id uuid primary key default gen_random_uuid(),
  title text not null default 'New Chat',
  user_id text not null default 'local',
  agent_id text not null default 'onyx',
  summary text default '',
  archived boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade,
  role text not null,
  content text not null,
  created_at timestamptz default now()
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  conversation_id uuid references conversations(id) on delete set null,
  title text not null,
  status text not null default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  conversation_id uuid references conversations(id) on delete set null,
  event_type text not null,
  content text not null,
  created_at timestamptz default now()
);

create table if not exists files (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  conversation_id uuid references conversations(id) on delete set null,
  name text not null,
  path text not null,
  size bigint default 0,
  content_type text default '',
  created_at timestamptz default now()
);

create table if not exists agent_state (
  id uuid primary key default gen_random_uuid(),
  agent_id text unique not null default 'onyx',
  user_id text not null default 'local',
  heartbeat timestamptz default now(),
  active_conversation_id uuid references conversations(id) on delete set null,
  working_summary text default '',
  goals jsonb default '[]',
  preferences jsonb default '{}',
  state_data jsonb default '{}',
  updated_at timestamptz default now()
);

-- Indexes
create index if not exists idx_messages_conversation on messages(conversation_id);
create index if not exists idx_messages_created on messages(created_at);
create index if not exists idx_conversations_user on conversations(user_id);
create index if not exists idx_tasks_user on tasks(user_id);
create index if not exists idx_events_user on events(user_id);
create index if not exists idx_files_user on files(user_id);

-- Enable Row Level Security
alter table conversations enable row level security;
alter table messages enable row level security;
alter table tasks enable row level security;
alter table events enable row level security;
alter table files enable row level security;
alter table agent_state enable row level security;

-- Permissive policies (tighten based on your auth setup)
create policy "Allow all" on conversations for all using (true);
create policy "Allow all" on messages for all using (true);
create policy "Allow all" on tasks for all using (true);
create policy "Allow all" on events for all using (true);
create policy "Allow all" on files for all using (true);
create policy "Allow all" on agent_state for all using (true);
