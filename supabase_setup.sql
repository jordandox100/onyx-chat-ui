-- ONYX Supabase Schema (with auth, shared folders, memories, beliefs, goals)
-- Run in Supabase SQL Editor

-- Users (auth)
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  password_hash text not null,
  is_admin boolean default false,
  created_at timestamptz default now()
);

-- Conversations
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

-- Messages
create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade,
  role text not null,
  content text not null,
  created_at timestamptz default now()
);

-- Memories (per user, private)
create table if not exists memories (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  conversation_id uuid references conversations(id) on delete set null,
  content text not null,
  memory_type text not null default 'fact',
  created_at timestamptz default now()
);

-- Beliefs (per user, private)
create table if not exists beliefs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  content text not null,
  confidence float default 0.8,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Goals (per user, private)
create table if not exists goals (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  title text not null,
  status text not null default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Tasks (per user, private)
create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  conversation_id uuid references conversations(id) on delete set null,
  title text not null,
  status text not null default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Events (per user)
create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  user_id text not null default 'local',
  conversation_id uuid references conversations(id) on delete set null,
  event_type text not null,
  content text not null,
  created_at timestamptz default now()
);

-- Files (per user)
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

-- Agent state
create table if not exists agent_state (
  id uuid primary key default gen_random_uuid(),
  agent_id text unique not null default 'onyx',
  user_id text not null default 'local',
  heartbeat timestamptz default now(),
  working_summary text default '',
  goals jsonb default '[]',
  preferences jsonb default '{}',
  state_data jsonb default '{}',
  updated_at timestamptz default now()
);

-- Shared folders
create table if not exists shared_folders (
  id uuid primary key default gen_random_uuid(),
  name text not null default 'Shared',
  owner_username text not null,
  partner_username text not null,
  created_at timestamptz default now()
);

-- Shared items
create table if not exists shared_items (
  id uuid primary key default gen_random_uuid(),
  folder_id uuid references shared_folders(id) on delete cascade,
  added_by text not null,
  content text not null,
  content_type text default 'text',
  created_at timestamptz default now()
);

-- Indexes
create index if not exists idx_users_username on users(username);
create index if not exists idx_messages_conversation on messages(conversation_id);
create index if not exists idx_memories_user on memories(user_id);
create index if not exists idx_beliefs_user on beliefs(user_id);
create index if not exists idx_goals_user on goals(user_id);
create index if not exists idx_tasks_user on tasks(user_id);
create index if not exists idx_events_user on events(user_id);
create index if not exists idx_files_user on files(user_id);
create index if not exists idx_shared_folders_owner on shared_folders(owner_username);
create index if not exists idx_shared_folders_partner on shared_folders(partner_username);
create index if not exists idx_shared_items_folder on shared_items(folder_id);

-- RLS
alter table users enable row level security;
alter table conversations enable row level security;
alter table messages enable row level security;
alter table memories enable row level security;
alter table beliefs enable row level security;
alter table goals enable row level security;
alter table tasks enable row level security;
alter table events enable row level security;
alter table files enable row level security;
alter table agent_state enable row level security;
alter table shared_folders enable row level security;
alter table shared_items enable row level security;

-- Permissive policies (tighten with real Supabase Auth later)
create policy "Allow all" on users for all using (true);
create policy "Allow all" on conversations for all using (true);
create policy "Allow all" on messages for all using (true);
create policy "Allow all" on memories for all using (true);
create policy "Allow all" on beliefs for all using (true);
create policy "Allow all" on goals for all using (true);
create policy "Allow all" on tasks for all using (true);
create policy "Allow all" on events for all using (true);
create policy "Allow all" on files for all using (true);
create policy "Allow all" on agent_state for all using (true);
create policy "Allow all" on shared_folders for all using (true);
create policy "Allow all" on shared_items for all using (true);
