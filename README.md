# Emergency Command Center

A unified Streamlit operations console for emergency incident management: intake,
prioritization, dispatch/tracking, resource management and historical analytics.

## Features

- **Incident Intake** - register incidents through fully validated input.
- **Priority Board** - rank open incidents using a randomized quick sort
  (priority score, severity or report time) with live sorting statistics.
- **Dispatch & Tracking** - greedy nearest-responder assignment, a strict status
  lifecycle (`open -> assigned -> in_progress -> closed`) and a LIFO undo stack.
- **Resource Management** - manage responders with a custom hash table and
  binary search.
- **Analytics Dashboard** - historical KPIs, resolution-time charts and a live
  zone map combining incidents and resources.

All modules share one live `CommandCenter` state so incidents created in the
intake page immediately appear on the priority board, dispatch console and
resources page. New incidents are also persisted to `data/incidents.csv` so the
analytics dashboard reflects operational activity.

## Project structure

```
Emergency-Command-Center/
├── app.py                     # Streamlit entry point (Home)
├── pages/                     # Multipage navigation
│   ├── 1_Incident_Intake.py
│   ├── 2_Priority_Board.py
│   ├── 3_Dispatch_Tracking.py
│   ├── 4_Resource_Management.py
│   └── 5_Analytics_Dashboard.py
├── core/                      # Domain, algorithms and data structures
│   ├── incident.py            # Incident model + validation
│   ├── incident_queue.py      # Queue (FIFO) data structure
│   ├── incident_manager.py    # Queue manager + binary search lookup
│   ├── priority.py            # Priority score calculation
│   ├── sorting.py             # Randomized quick sort
│   ├── responders.py          # Responder hierarchy
│   ├── resource_manager.py    # Hash table + binary search
│   ├── dispatch.py            # Dispatch engine + action history stack
│   ├── storage.py             # CSV persistence layer
│   └── command_center.py      # Shared live application state
├── data/                      # incidents.csv, responders.csv
├── .streamlit/config.toml     # Theme / server config
└── requirements.txt
```

## Getting started

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL printed in the terminal and use the sidebar to navigate
between modules.

## Data files

- `data/incidents.csv` - historical incident records used by the analytics page.
- `data/responders.csv` - responder roster loaded into the resource manager.

## Notes

- `Incident.id_counter` assigns sequential IDs such as `INC0001`.
- Distance for greedy dispatch is computed from a small coordinate map of known
  zones/cities (see `DispatchEngine.LOCATION_COORDS`).
