# Technology Stack

The Expense Tracker will use the following technologies:

| Technology     | Purpose                                                                       |
| -------------- | ----------------------------------------------------------------------------- |
| **HTML**       | Create the structure of the application pages and forms.                      |
| **CSS**        | Style the application and make it simple and easy to use.                     |
| **JavaScript** | Handle interactions such as form actions, filtering, and delete confirmation. |
| **Flask**      | Handle the application logic, user authentication, and expense operations.    |
| **SQLite**     | Store user accounts and expense records.                                      |

## Version 2 Stack Review

The current stack remains sufficient for the Version 2 release. Monthly budget tracking and category analytics can be implemented using the existing Flask backend, SQLite data layer, and HTML/CSS/JavaScript frontend without changing the project’s core technology decisions.

### Recommended approach

- Keep Flask for all server-side calculations and route logic.
- Keep SQLite for budget persistence and analytics queries.
- Use simple HTML/CSS/JavaScript for dashboard panels, progress bars, and category summaries.
- Use a lightweight charting library only if the project later decides that visual graphs are required beyond basic summary bars.

### Recommendation

No additional mandatory dependency is required for the Version 2 scope. A chart library such as Chart.js may be considered later as an optional enhancement, but the minimum viable implementation can be delivered without introducing a new package.
