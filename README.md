# Pitcher Analysis and Fatigue

Hello Friends,

Being rather passionate about the analytical side of baseball I decided to begin a project on pitcher fatigue. However, while doing so I realized I could quite easily create a Major League Baseball (MLB) pitcher summary for the many advanced statistics I am analyzing. 

## Current Status

The overarching and incomplete goal of this project is to find trends in a pitcher's level of fatigue throughout an MLB season. This analysis could give insight to MLB managers on how they should use their pitcher to be most effective throughout a season and reduce risk of injury. 


While incomplete, this project currently works as a dashboard that visualizes the performance of MLB starting pitchers during the 2024 season. To do this it uses a combination of MLB Statcast and Fangraphs APIs to access pitch by pitch data across all of the MLB.

- Rolling pitch usage trends  
- Velocity distributions by pitch type  
- Horizontal and vertical break plots  
- Advanced pitch metrics (e.g., whiff rate, xwOBA, chase rate)

The dashboard is wildly unpolished and implemented using Python, Pandas, Seaborn, and Matplotlib.

\includegraphics[]{pitching_dashboard.pdf}
