# --- Admin / User Manager Helpers ---

def add_admin(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        admin_roles = guild.setdefault("admin_roles", [])
        if str(user_or_role_id) not in admin_roles:
            admin_roles.append(str(user_or_role_id))
    else:
        admins = guild.setdefault("admins", [])
        if str(user_or_role_id) not in admins:
            admins.append(str(user_or_role_id))
    save_data(data)

def remove_admin(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        admin_roles = guild.setdefault("admin_roles", [])
        if str(user_or_role_id) in admin_roles:
            admin_roles.remove(str(user_or_role_id))
    else:
        admins = guild.setdefault("admins", [])
        if str(user_or_role_id) in admins:
            admins.remove(str(user_or_role_id))
    save_data(data)

def add_user_manager(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        manager_roles = guild.setdefault("user_manager_roles", [])
        if str(user_or_role_id) not in manager_roles:
            manager_roles.append(str(user_or_role_id))
    else:
        managers = guild.setdefault("user_managers", [])
        if str(user_or_role_id) not in managers:
            managers.append(str(user_or_role_id))
    save_data(data)

def remove_user_manager(data, guild_id: int, user_or_role_id: int, is_role=False):
    guild = data.setdefault("guilds", {}).setdefault(str(guild_id), {})
    if is_role:
        manager_roles = guild.setdefault("user_manager_roles", [])
        if str(user_or_role_id) in manager_roles:
            manager_roles.remove(str(user_or_role_id))
    else:
        managers = guild.setdefault("user_managers", [])
        if str(user_or_role_id) in managers:
            managers.remove(str(user_or_role_id))
    save_data(data)
