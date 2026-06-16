def retrieve_relevant_professors(query, professors, top_k=5):
    """Retrieve professors relevant to a query using keyword matching."""
    
    professor_keywords = ["professor", "prof", "teacher", "instructor", "teach", "class", "course", "csc", "cpe", "who", "rating", "recommend"]
    query_lower = query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 2]
    
    
    if not any(keyword in query_lower for keyword in professor_keywords):
        return []
    
    scored = []

    for prof in professors:
        score = 0
        first = prof['firstName'].lower()
        last = prof['lastName'].lower()

        # Match by first or last name individually
        for word in query_words:
            if word in first or word in last:
                score += 10

        # Match by course
        for course in prof.get("courses", []):
            if any(word in course.lower() for word in query_words):
                score += 5

        # Match by tags
        for tag in prof.get("tags", {}).keys():
            if any(word in tag.lower() for word in query_words):
                score += 2

        if score > 0:
            scored.append((score, prof))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [prof for score, prof in scored[:top_k]]