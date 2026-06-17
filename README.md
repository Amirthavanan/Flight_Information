# Flight_Information
Realtime flight details searching application - <a href="https://flightinformation-7ltu4zggouufxuz3e7qlbf.streamlit.app/">Click here</a><br>
<h3>Description</h3>
A dynamic, end-to-end web application that allows users to search for real-time flight information globally. The application integrates with a live search API to pull real flight options (including airlines, duration, and pricing) and automatically stores user search history and flight details into a cloud-hosted relational database. It also features a comprehensive, interactive analytics dashboard that visualizes search trends, popular flight routes, and average pricing using advanced data manipulation and charting techniques.
<br>
The application is styled with a custom, premium UI featuring dark-mode gradients, glassmorphism effects, and responsive interactions, offering an enterprise-grade user experience.
<h3>Tech Stack</h3>
<ul>
  <li>Frontend / User Interface: Streamlit (Python web framework), Custom CSS (for glassmorphism, animations, and gradient styling)
</li>
  <li>Backend / Core Logic: Python
</li>
  <li>Data Processing & Analytics: Pandas (for data manipulation, filtering, and metric calculation)
</li>
  <li>  Database Management: TiDB (Cloud-hosted MySQL-compatible database)
</li>
  <li>Database Connector / ORM: SQLAlchemy & PyMySQL (with connection pooling)
</li>
  <li>External APIs: SerpAPI (Google Flights Engine) for retrieving live airline and flight data via HTTP requests (requests library)
</li>
  <li>Deployment: GitHub, Streamlit Community Cloud (with secure Streamlit Secrets management)
</li>
</ul>



<h3>Preview:</h3><br>
<img src="image.png">
<img src="image1.png">
