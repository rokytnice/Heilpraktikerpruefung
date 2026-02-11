import subprocess
import time
import xml.etree.ElementTree as ET

def dump_ui(output_path="window_dump.xml"):
    """Dumps the current UI hierarchy to an XML file."""
    try:
        subprocess.run(["adb", "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], check=True)
        subprocess.run(["adb", "pull", "/sdcard/window_dump.xml", output_path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_node_text(xml_path, resource_id=None, text_contains=None):
    """Parses XML and returns text of matching node."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        for node in root.iter("node"):
            if resource_id and node.attrib.get("resource-id") == resource_id:
                return node.attrib.get("text")
            if text_contains and text_contains in node.attrib.get("text", ""):
                return node.attrib.get("text")
        return None
    except Exception:
        return None

def tap(x, y):
    """Simulates a tap input at coordinates (x, y)."""
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])

def screencap(output_path="screen.png"):
    """Captures a screenshot."""
    subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"])
    subprocess.run(["adb", "pull", "/sdcard/screen.png", output_path])
