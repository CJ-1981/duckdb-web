"""
Permission definitions for Role-Based Access Control (RBAC).

@MX:NOTE: Central permission constants following SPEC-PLATFORM-001 P2-T003
@MX:SPEC: SPEC-PLATFORM-001 P2-T003
"""

# Data Permissions
DATA_READ = "data:read"
DATA_WRITE = "data:write"
DATA_DELETE = "data:delete"
DATA_EXPORT = "data:export"

# Jobs Permissions
JOBS_CREATE = "jobs:create"
JOBS_READ = "jobs:read"
JOBS_CANCEL = "jobs:cancel"

# Admin Permissions
USERS_MANAGE = "users:manage"
SYSTEM_CONFIG = "system:config"

# Permission Groups
DATA_PERMISSIONS = [
    DATA_READ,
    DATA_WRITE,
    DATA_DELETE,
    DATA_EXPORT,
]

JOBS_PERMISSIONS = [
    JOBS_CREATE,
    JOBS_READ,
    JOBS_CANCEL,
]

ADMIN_PERMISSIONS = [
    USERS_MANAGE,
    SYSTEM_CONFIG,
]

# All permissions (for reference)
ALL_PERMISSIONS = DATA_PERMISSIONS + JOBS_PERMISSIONS + ADMIN_PERMISSIONS
