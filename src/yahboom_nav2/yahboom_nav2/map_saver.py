import os
import subprocess
from ament_index_python.packages import get_package_share_directory

def main():
    package_name = 'yahboom_nav2'
    
    try:
        # Get the share directory (usually in install/package_name/share/package_name)
        share_dir = get_package_share_directory(package_name)
        
        # Default fallback to share directory
        map_dir = os.path.join(share_dir, 'maps')
        
        # Try to find the source directory for persistence
        # Typical workspace structure: 
        # workspace/
        #   src/package_name/
        #   install/package_name/share/package_name/
        
        # Go up from share/package_name -> share -> package_name -> install -> workspace
        # This is a bit brittle but common for local development
        workspace_dir = os.path.abspath(os.path.join(share_dir, '..', '..', '..', '..'))
        src_map_dir = os.path.join(workspace_dir, 'src', package_name, 'maps')
        
        if os.path.exists(src_map_dir):
            map_dir = src_map_dir
            print(f"Found source directory at: {map_dir}")
        else:
            # Try specific path if standard search fails
            src_map_dir = os.path.join(workspace_dir, 'src', 'ros2', 'src', package_name, 'maps')
            if os.path.exists(src_map_dir):
                map_dir = src_map_dir
                print(f"Found source directory at: {map_dir}")
        
        map_path = os.path.join(map_dir, 'map')
        
        print(f"Saving map to: {map_path}.yaml")
        
        # Ensure the directory exists
        os.makedirs(map_dir, exist_ok=True)
        
        cmd = [
            'ros2', 'run', 'nav2_map_server', 'map_saver_cli',
            '-f', map_path
        ]
        
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error saving map: {e}")

if __name__ == '__main__':
    main()
