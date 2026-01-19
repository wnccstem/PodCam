# ---------------------------- WEB PAGE HTML ------------------------------- #
""" This is the HTML code for the web page for testing in a browser.
 It's a multi-line string (triple quotes) so you can write it like a document."""
PAGE = """
<html>
<head>
<title>PodsInSpace - Pod Camera Monitor</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { 
    font-family: Arial, sans-serif; 
    margin: 20px; 
    background-color: #f0f0f0; 
}
.container { 
    max-width: 900px; 
    margin: 0 auto; 
    background-color: white; 
    padding: 20px; 
    border-radius: 10px; 
    box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
}
.camera-box {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin: 20px 0;
}
.camera-title {
    text-align: center;
    margin-bottom: 10px;
    font-weight: bold;
    font-size: 1.2em;
    color: #555;
}
.camera-stream {
    width: 100%;
    height: auto;
    border: 2px solid #333;
    border-radius: 4px;
    display: block;
}
.info { 
    text-align: center;
    margin-top: 20px; 
    padding: 15px; 
    background-color: #e6f3ff; 
    border-radius: 5px; 
    font-size: 14px;
    color: #666;
}
</style>
</head>
<body>
<div class="container">
    <h1>PodsInSpace - Pod Camera Monitor</h1>
    <p>Live video feed from Pod camera</p>
    
    <div class="camera-box">
        <div class="camera-title">Pod Camera - Live View</div>
        <img src="/stream0.mjpg" class="camera-stream" alt="Pod Camera Stream">
    </div>
    
    <div class="info">
        <strong>Stream Info:</strong><br>
        Resolution: 1280x720 | Quality: 85% | Frame Rate: Up to 20 FPS<br>
        Optimized for monitoring with reduced bandwidth usage<br>
        <p>Direct stream URL: <a href="/stream0.mjpg">Pod Camera Stream</a></p>
        <p>
            <strong>White Balance:</strong>
            <a href="/wb/calibrate">Calibrate (full frame)</a> |
            <a href="/wb/calibrate?roi=center&size=0.45">Calibrate Center ROI</a> |
            <a href="/wb/preview?roi=center&size=0.45" target="_blank">Preview ROI Gains</a> |
            <a href="/wb/locked">Lock</a> |
            <a href="/wb/auto">Auto</a> |
            <a href="/wb/off">Off</a> |
            <a href="/wb/clear">Clear Calibration</a>
        </p>
    </div>
</div>
</body>
</html>
"""