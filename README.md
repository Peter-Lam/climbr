# Climbing-Tracker
Tracking and visualizing climbing progression post COVID-19. 

## The Goal
- Log climbing sessions and problems
- Use logs to visualize climbing trends, patterns, and statistics
    - Progression in grades over time
    - What's your flash grade? project grade?
    - Hard problem climbed outdoors
    - Most common climbing discipline (Lead, Bouldering, Trad)
    - Most common climbing style
    - Weakest climbing style
- Use data to influence your training regime and pinpoint weaknesses

## TO DO
- [ ] Develop Python scripts to automate logging process 
- [ ] Containerize scripts, elasticsearch, and kibana for easy plug and play capabilities
- [ ] Investigate hybrid application stacks
- [ ] Develop

### Logging Capabilities
- Track number of problems/routes completed or attempted in session
    - Grade
    - Onsight / Flash / Redpoint / Repeat / Attempts
- Track specific climbs
    - Useful for tracking progress on a project
- Who you climb with
- Average session length
- Heatmap / World map of locations climbed
- Track climbs over time
- Hardest climb completed
- Project grade
- Flash grade
- Filter by location, climbing style, climbing disciplines
- Track project progress

Design choices:
- Not personally tracking Onsights for indoor bouldering (Completing a problem on your first try without prior knowledge of beta)
- properties file for preferences V-scale, Font... ?? maybe not