# 📌 ReminderBot

### General Info
This is **Test Version 0.0.8** of ReminderBot.  
⚠️ **Warning:** This is a <ins>**TEST BUILD**</ins>. If you want a stable version, please check the **main branch**, which always contains a working release.  

ReminderBot is a Discord bot designed to help users and communities schedule and manage reminders.  
It supports **multiple delivery modes** (DMs, text channels, forum posts) and has a flexible **role-based permission system**:  
- **Admins** → Manage everything (users, roles, all reminders)  
- **User Managers** → Moderate user reminders and set guild defaults  
- **Users** → Manage their own reminders privately  

🔗 Development is tracked in Todoist: [ReminderBot Project Board](https://app.todoist.com/app/task/reminderbot-totallity-6crrqjjG8v8xpXhp)  

---

### Features (Current)
- Create reminders with custom delivery (DM, channel, forum, or both)  
- List and cancel reminders with role-based permissions  
- Logging of all actions per guild  
- Missed reminders get delivered once the bot is back online  
- Guild-separated data for privacy

If you have any extra suggestions, please suggest them in discussions!  

---

### Instructions
1. Open a terminal in the `reminderbot` root directory.  
2. Run:  

   ```bash
   python bot.py
3. Make sure your bot token is set (the one in past commits is reset and non-functional).

📜 This project is licensed under Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

### 💡 Suggestions & Contributions

This project is still in active development, and feedback is welcome!
If you have ideas for features, improvements, or notice bugs:
- Open an Issue in the repository
- Or create a Pull Request with your proposed changes

Please keep in mind this branch is experimental, so features may change quickly.

### My current plans:

## ✅ Completed
- [x] `/reminder` command with delivery modes (`dm`, `channel`, `forum`, `both`)  
- [x] `/reminderlist` with role-based visibility (Admin Managers, User Managers, regular users)  
- [x] `/remindercancel` with proper permission checks  
- [x] Guild-isolated storage for reminders  
- [x] Role-based permissions:
  - **Admin Managers** → Full control (manage admins, manage all reminders)  
  - **User Managers** → Limited control (moderate reminders, toggle guild defaults)  
- [x] Logging per guild (reminder creation, cancellation, delivery, missed reminders)  
- [x] Forum post support for reminders  

---

## 🔹 High Priority
- [ ] **Default Delivery Mode (Guild Setting)**  
  - Toggleable by **User Managers**  
  - Used when `/reminder` is called without specifying delivery  

- [ ] **Improved Reminder Listing**  
  - Paginate `/reminderlist` for large lists  
  - Show delivery mode, creator, and due time in a clean embed format  

- [ ] **Better Storage & Persistence**  
  - Migrate from JSON to SQLite (or hybrid JSON+SQLite)  
  - Ensures reminders survive restarts and scales better  

---

## 🔸 Medium Priority
- [ ] **Reminder Editing**  
  - Command to update an existing reminder (time, message, delivery mode)  

- [ ] **Cleaner Expiry**  
  - Auto-clean delivered/expired reminders more efficiently  

- [ ] **Error Handling**  
  - Handle deleted users, channels, roles  
  - Fallback to DM if channel/forum is missing  

- [ ] **Manager Lists**  
  - Commands to show which roles/users are **Admins** vs **User Managers**  

---

## ⚪ Low Priority (Future Ideas)
- [ ] **Recurring Reminders**  
  - Daily, weekly, or custom intervals  

- [ ] **Reminder Search**  
  - Search by keyword or user  

- [ ] **Reminder Stats**  
  - Show number of reminders per user/guild  

- [ ] **Optional Acknowledgements**  
  - DM receipt confirmation  
  - Reaction ✅ in channel/forum when reminder fires  

- [ ] **Dashboard (Future)**  
  - Web-based dashboard for managing reminders  
  - Guild settings + reminder editing in UI  
