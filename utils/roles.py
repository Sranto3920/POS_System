class Role:
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"

    ALL = (ADMIN, MANAGER, CASHIER)

    LABELS = {
        ADMIN: "Administrator",
        MANAGER: "Manager",
        CASHIER: "Cashier",
    }

    # Existing DB may store title-case role names.
    _ALIASES = {
        "admin": ADMIN,
        "administrator": ADMIN,
        "manager": MANAGER,
        "cashier": CASHIER,
    }

    @classmethod
    def normalize(cls, role):
        if not role:
            return cls.CASHIER
        key = role.strip().lower()
        return cls._ALIASES.get(key, key)

    @classmethod
    def label(cls, role):
        return cls.LABELS.get(cls.normalize(role), role.title())

    @classmethod
    def is_valid(cls, role):
        return cls.normalize(role) in cls.ALL

    @classmethod
    def matches(cls, user_role, *allowed_roles):
        normalized_user = cls.normalize(user_role)
        return normalized_user in {cls.normalize(r) for r in allowed_roles}
