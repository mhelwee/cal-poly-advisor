CS_REQUIREMENTS = {
    "major_courses": [
        "CSC 1000",   # Computing Majors Orientation
        "CSC 1001",   # Fundamentals of Computer Science
        "CSC 1024",   # Introduction to Computing
        "CSC 2001",   # Data Structures
        "CSC 2050",   # System Software Mechanics
        "CPE 2300",   # Introduction to Computer Systems
        "CSC 3001",   # Modern Application Development
        "CSC 3100",   # Software Engineering
        "CSC 3201",   # Introduction to Computer Security
        "CSC 3300",   # Programming Languages
        "CSC 3449",   # Algorithms and Complexity
        "CSC 4553",   # Introduction to Operating Systems
    ],
    "support_courses": [
        "MATH 1151",  # Linear Algebra
        "MATH 1261",  # Calculus I
        "MATH 1262",  # Calculus II
        "MATH 2031",  # Transition to Advanced Mathematics
        "STAT 3210",  # Engineering Statistics
        "PHIL 3323",  # Ethics, Science, and Technology
        "WGQS 3350",  # Gender, Race, Culture, Science, and Technology
    ],
    "senior_project": [
        "CSC 4460 or CSC 4461 (or approved alternative)"
    ],
    "technical_electives": "23 units required from approved elective list",
    "total_units": 120
}

PREREQUISITE_CHAIN = {
    "CSC 2001": ["CSC 1001"],
    "CSC 2050": ["CSC 1001"],
    "CPE 2300": ["CSC 1024"],
    "CSC 3001": ["CSC 2001"],
    "CSC 3100": ["CSC 3001"],
    "CSC 3201": ["CSC 2001"],
    "CSC 3300": ["CSC 2001"],
    "CSC 3449": ["CSC 2001", "MATH 2031"],
    "CSC 4553": ["CSC 2050", "CPE 2300"],
}

COURSE_NAMES = {
    "CSC 1000": "Computing Majors Orientation",
    "CSC 1001": "Fundamentals of Computer Science",
    "CSC 1024": "Introduction to Computing",
    "CSC 2001": "Data Structures",
    "CSC 2050": "System Software Mechanics",
    "CPE 2300": "Introduction to Computer Systems",
    "CSC 3001": "Modern Application Development",
    "CSC 3100": "Software Engineering",
    "CSC 3201": "Introduction to Computer Security",
    "CSC 3300": "Programming Languages",
    "CSC 3449": "Algorithms and Complexity",
    "CSC 4553": "Introduction to Operating Systems",
    "MATH 1151": "Linear Algebra",
    "MATH 1261": "Calculus I",
    "MATH 1262": "Calculus II",
    "MATH 2031": "Transition to Advanced Mathematics",
    "STAT 3210": "Engineering Statistics",
    "PHIL 3323": "Ethics, Science, and Technology",
    "WGQS 3350": "Gender, Race, Culture, Science, and Technology",
}