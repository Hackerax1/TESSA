import psutil
import platform
import json

class HardwareDetector:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.cpu_info = self.get_cpu_info()
        self.memory_info = self.get_memory_info()
        self.disk_info = self.get_disk_info()

    def get_system_info(self):
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }

    def get_cpu_info(self):
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max,
            "min_frequency": psutil.cpu_freq().min,
            "current_frequency": psutil.cpu_freq().current,
            "cpu_usage": psutil.cpu_percent(interval=1)
        }

    def get_memory_info(self):
        svmem = psutil.virtual_memory()
        return {
            "total": svmem.total,
            "available": svmem.available,
            "used": svmem.used,
            "percentage": svmem.percent
        }

    def get_disk_info(self):
        partitions = psutil.disk_partitions()
        disk_info = []
        for partition in partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percentage": usage.percent
            })
        return disk_info

    def get_hardware_summary(self):
        return {
            "system_info": self.system_info,
            "cpu_info": self.cpu_info,
            "memory_info": self.memory_info,
            "disk_info": self.disk_info
        }

    def save_summary_to_file(self, file_path="hardware_summary.json"):
        summary = self.get_hardware_summary()
        with open(file_path, "w") as file:
            json.dump(summary, file, indent=4)

if __name__ == "__main__":
    detector = HardwareDetector()
    detector.save_summary_to_file()