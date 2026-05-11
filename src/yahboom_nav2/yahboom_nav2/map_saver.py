import os
import subprocess
from ament_index_python.packages import get_package_share_directory


def main():
    package_name = 'yahboom_nav2'

    try:
        share_dir = get_package_share_directory(package_name)
        workspace_dir = os.path.abspath(os.path.join(share_dir, '..', '..', '..', '..'))

        # Prefer source directory so the map persists across rebuilds
        map_dir = os.path.join(workspace_dir, 'src', package_name, 'maps')
        if not os.path.exists(map_dir):
            map_dir = os.path.join(share_dir, 'maps')  # fallback: install space

    except Exception:
        map_dir = os.path.join(os.getcwd(), 'maps')

    os.makedirs(map_dir, exist_ok=True)
    map_path = os.path.join(map_dir, 'map')

    print(f'Saving map to: {map_path}.yaml')
    subprocess.run([
        'ros2', 'run', 'nav2_map_server', 'map_saver_cli',
        '-f', map_path,
    ])


if __name__ == '__main__':
    main()
