### Readme File of reminderbot
## General info:
This is test ver. 08 of reminderbot which is now a test bot that makes reminders, warning it is a <ins>**TEST BUILD**</ins>, so if you want a working version, please go to the main branch, it will allways be working.  
  
Todoist: https://app.todoist.com/app/task/reminderbot-totallity-6crrqjjG8v8xpXhp  
  
## Instructions:  
Open terminal and type: "python bot.py" in directory reminder bot, which is top-level.
This software uses the license Attribution-NonCommercial 4.0 International
Also, no the token in commits doesn't work, it is now reset.  

## My current plans:
# 📝 To-Do / Roadmap

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
