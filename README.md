# 📌 ReminderBot

### General Info

This is **Test Version 0.8** of ReminderBot.  
⚠️ **Warning:** This is a <ins>**TEST BUILD**</ins>. If you want a stable version, please check the **main branch**.

ReminderBot is a Discord bot designed to help users and communities schedule and manage reminders.  
It supports **multiple delivery modes** (DMs, text channels, forum posts) and a **role-based permission system**:

* **Admins** → Full control, manage everything (users, roles, reminders)
* **User Managers** → Moderate user reminders, set guild defaults
* **Users** → Manage their own reminders privately

🔗 Development is tracked in Todoist: [ReminderBot Project Board](https://app.todoist.com/app/task/reminderbot-totallity-6crrqjjG8v8xpXhp)

---

### Features (Current)

**Core Reminder Features**
- Create reminders with message, target, and delivery ('dm', 'channel', 'forum', 'both')
- Cancel and list reminders (permission-based)
- Missed reminders delivered after bot comes back online
- Guild-separated data for privacy
- Thread-aware delivery with correct channel/thread ID

**Permission System**
- Admins: full control, manage admins, user managers, update channels, view guild defaults
- User Managers: moderate user reminders, set guild default delivery
- Users: manage own reminders privately

**Update & Announcement Features**
- Designate **update channels** per guild
- '/backend update' broadcasts messages to all configured update channels
- Fallback DM to guild owner if no update channel exists

**Backend / Dev Features**
- Hidden '/backend' command group (dev-only, backend guild only)
- Commands:
  - '/backend status' → uptime, loaded cogs, reminder count, log level
  - '/backend reload' → reload settings & cogs
  - '/backend restart' → soft restart
  - '/backend hardrestart' → full restart via launcher
  - '/backend stop' → stop bot and launcher
  - '/backend autorestart' → toggle crash auto-restart
  - '/backend listadmins' → list all Admins per guild
  - '/backend listusermanagers' → list all User Managers per guild
  - '/backend guilddefaults' → show default reminder delivery per guild
  - '/backend supportinvite' → DM guild owners/Admins with support invite

**Logging & Safety**
- Logs all actions per guild
- Handles deleted/missing users, channels, roles
- Ephemeral responses for backend commands
- Only dev IDs in backend guild can access hidden commands

**Launcher Features**
- Terminal commands: 'r' (restart bot), 'q' (quit bot/launcher)
- Prevents boot loops by clearing restart flag after each run
- Works with '/backend hardrestart' and '/backend stop'

---

### ⚡ Commands Overview

<details>
<summary><strong>🟢 User Commands</strong></summary>

| Command           | Description                 |
| ----------------- | --------------------------- |
| '/reminder'       | Set a reminder for yourself |
| '/reminderlist'   | List your reminders         |
| '/remindercancel' | Cancel your reminders       |

</details>

<details>
<summary><strong>🔵 User Manager Commands</strong></summary>

| Command               | Description                             |
| --------------------- | --------------------------------------- |
| '/reminderfor'        | Set a reminder for another user or role |
| '/listremindersfor'   | List reminders for a user or role       |
| '/cancelremindersfor' | Cancel reminders for a user or role     |
| '/setdefaultdelivery' | Set the guild default delivery mode     |

</details>

<details>
<summary><strong>🟣 Admin Commands</strong></summary>

| Command                | Description                                 |
| ---------------------- | ------------------------------------------- |
| '/addadmin'            | Add a user or role as Admin Manager         |
| '/removeadmin'         | Remove a user or role from Admin Managers   |
| '/listadmins'          | List all Admins and Admin roles             |
| '/addusermanager'      | Add a user or role as User Manager          |
| '/removeusermanager'   | Remove a user or role from User Managers    |
| '/listusermanagers'    | List all User Managers and roles            |
| '/setupdatechannel'    | Set a channel for bot updates/announcements |
| '/removeupdatechannel' | Remove an update channel                    |
| '/listupdatechannels'  | List all update channels                    |

</details>

<details>
<summary><strong>🟠 Dev/Host Commands</strong></summary>

|                     Command | Description                                                                 |
| --------------------------: | --------------------------------------------------------------------------- |
|           '/backend update' | Send update message to all guilds that have an update channel configured    |
|    '/backend guilddefaults' | Show the default reminder delivery mode for every guild the bot is in       |
|       '/backend listadmins' | List Admin users and Admin roles across all guilds                          |
| '/backend listusermanagers' | List User Manager users and roles across all guilds                         |
|           '/backend reload' | Reload settings and command cogs                                            |
|           '/backend status' | Return bot status (uptime, loaded cogs, reminder count, log level)          |
|       '/backend restart'    | Soft restart (reload cogs without stopping the bot)                         |
|       '/backend hardrestart'| Fully restart the bot process                                               |
|      '/backend stop'        | Stop the bot and launcher completely                                        |
|      '/backend autorestart' | Toggle automatic crash restart                                              |
|    '/backend supportinvite' | DM all guild owners and configured Admins with support server invite        |

All of these are hidden!

</details>

---

### Instructions

1. Open a terminal in the 'reminderbot' root directory.
2. Run:

   `
   python launcher.py
`

3. Make sure your 'settings.json' and 'launcher_control.json' are properly configured.
4. For hosting, join the support server: [https://discord.gg/CwSqSBzXPn](https://discord.gg/CwSqSBzXPn)

📜 This project is licensed under Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

---

### 💡 Suggestions & Contributions

This project is still in active development. Feedback is welcome!
Open an **Issue** or create a **Pull Request** with proposed changes.

---

### Current Plans

#### ✅ Completed

* Core reminder creation, listing, and cancellation
* Delivery modes: DM, channel, forum, both
* Role-based permissions (Admins, User Managers, Users)
* Logging per guild
* Update Channels & Guild Defaults
* Soft & Hard restarts, launcher integration

#### 🔹 High Priority

* Better storage/persistence (JSON → SQLite or hybrid)

#### 🔸 Medium Priority

* Reminder editing
* Cleaner expiry & delivery
* Error handling for deleted/missing entities

#### ⚪ Low Priority (Future Ideas)

* Recurring reminders
* Reminder search & stats
* Optional acknowledgements
* Web-based dashboard
