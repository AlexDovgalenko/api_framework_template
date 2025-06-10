USER_DETAILS_LIST = [
    {
        "id": "1",
        "username": "alice.smith",
        "full_name": "Alice Smith",
        "is_active": True,
        "contact": {
            "email": "alice.smith@example.com",
            "phone": "+1234567890",
            "addresses": [
                {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "USA",
                    "is_primary": True,
                }
            ],
        },
        "permissions": [{"name": "user:read", "level": 1}],
    },
    {
        "id": "2",
        "username": "bob.johnson",
        "full_name": "Bob Johnson",
        "is_active": True,
        "contact": {
            "email": "bob.johnson@example.com",
            "phone": "+1234567891",
            "addresses": [],
        },
        "permissions": [],
    },
    {
        "id": "3",
        "username": "charlie.brown",
        "full_name": "Charlie Brown",
        "is_active": True,
        "contact": {
            "email": "charlie.brown@example.com",
            "phone": "+1987654321",
            "addresses": [
                {
                    "street": "456 Oak Ave",
                    "city": "Los Angeles",
                    "state": "CA",
                    "zip_code": "90001",
                    "country": "USA",
                    "is_primary": True,
                }
            ],
        },
        "permissions": [{"name": "user:write", "level": 2}],
    },
    {
        "id": "4",
        "username": "diana.davis",
        "full_name": "Diana Davis",
        "is_active": False,
        "contact": {
            "email": "diana.davis@example.com",
            "phone": "+1987654324",
            "addresses": [],
        },
        "permissions": [],
    },
]
