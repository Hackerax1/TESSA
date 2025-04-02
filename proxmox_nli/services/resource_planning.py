"""
Resource Planning Service for Proxmox NLI.

This service provides tools for resource planning, including:
- Pre-setup resource calculator
- Disk space forecasting
- Hardware recommendations engine
"""

import json
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from proxmox_nli.utils.config import get_config_dir


class ResourcePlanningService:
    """Service for resource planning and hardware recommendations."""

    def __init__(self):
        """Initialize the resource planning service."""
        self.config_dir = os.path.join(get_config_dir(), "resource_planning")
        self.plans_dir = os.path.join(self.config_dir, "plans")
        self.hardware_db_path = os.path.join(self.config_dir, "hardware_db.json")
        self.vm_profiles_path = os.path.join(self.config_dir, "vm_profiles.json")
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.plans_dir, exist_ok=True)
        
        # Initialize hardware database if it doesn't exist
        if not os.path.exists(self.hardware_db_path):
            self._initialize_hardware_db()
        
        # Initialize VM profiles if they don't exist
        if not os.path.exists(self.vm_profiles_path):
            self._initialize_vm_profiles()
    
    def _initialize_hardware_db(self):
        """Initialize the hardware database with default values."""
        hardware_db = {
            "cpu": {
                "intel_core_i3": {
                    "name": "Intel Core i3",
                    "cores_per_socket": 2,
                    "threads_per_core": 2,
                    "performance_score": 6000,
                    "tdp": 65,
                    "suitable_for": ["home_lab", "small_office"],
                    "virtualization_support": True
                },
                "intel_core_i5": {
                    "name": "Intel Core i5",
                    "cores_per_socket": 4,
                    "threads_per_core": 2,
                    "performance_score": 10000,
                    "tdp": 95,
                    "suitable_for": ["home_lab", "small_office", "medium_office"],
                    "virtualization_support": True
                },
                "intel_core_i7": {
                    "name": "Intel Core i7",
                    "cores_per_socket": 6,
                    "threads_per_core": 2,
                    "performance_score": 14000,
                    "tdp": 125,
                    "suitable_for": ["home_lab", "small_office", "medium_office", "large_office"],
                    "virtualization_support": True
                },
                "intel_core_i9": {
                    "name": "Intel Core i9",
                    "cores_per_socket": 8,
                    "threads_per_core": 2,
                    "performance_score": 18000,
                    "tdp": 125,
                    "suitable_for": ["medium_office", "large_office", "data_center"],
                    "virtualization_support": True
                },
                "intel_xeon_e": {
                    "name": "Intel Xeon E",
                    "cores_per_socket": 4,
                    "threads_per_core": 2,
                    "performance_score": 12000,
                    "tdp": 80,
                    "suitable_for": ["home_lab", "small_office", "medium_office"],
                    "virtualization_support": True
                },
                "intel_xeon_silver": {
                    "name": "Intel Xeon Silver",
                    "cores_per_socket": 8,
                    "threads_per_core": 2,
                    "performance_score": 16000,
                    "tdp": 85,
                    "suitable_for": ["medium_office", "large_office", "data_center"],
                    "virtualization_support": True
                },
                "intel_xeon_gold": {
                    "name": "Intel Xeon Gold",
                    "cores_per_socket": 16,
                    "threads_per_core": 2,
                    "performance_score": 22000,
                    "tdp": 150,
                    "suitable_for": ["large_office", "data_center"],
                    "virtualization_support": True
                },
                "amd_ryzen_5": {
                    "name": "AMD Ryzen 5",
                    "cores_per_socket": 6,
                    "threads_per_core": 2,
                    "performance_score": 12000,
                    "tdp": 65,
                    "suitable_for": ["home_lab", "small_office", "medium_office"],
                    "virtualization_support": True
                },
                "amd_ryzen_7": {
                    "name": "AMD Ryzen 7",
                    "cores_per_socket": 8,
                    "threads_per_core": 2,
                    "performance_score": 16000,
                    "tdp": 105,
                    "suitable_for": ["home_lab", "small_office", "medium_office", "large_office"],
                    "virtualization_support": True
                },
                "amd_ryzen_9": {
                    "name": "AMD Ryzen 9",
                    "cores_per_socket": 12,
                    "threads_per_core": 2,
                    "performance_score": 20000,
                    "tdp": 105,
                    "suitable_for": ["medium_office", "large_office", "data_center"],
                    "virtualization_support": True
                },
                "amd_epyc_7002": {
                    "name": "AMD EPYC 7002",
                    "cores_per_socket": 16,
                    "threads_per_core": 2,
                    "performance_score": 24000,
                    "tdp": 120,
                    "suitable_for": ["large_office", "data_center"],
                    "virtualization_support": True
                }
            },
            "memory": {
                "ddr4_2400": {
                    "name": "DDR4-2400",
                    "performance_score": 2400,
                    "ecc_support": False
                },
                "ddr4_3200": {
                    "name": "DDR4-3200",
                    "performance_score": 3200,
                    "ecc_support": False
                },
                "ddr4_3600": {
                    "name": "DDR4-3600",
                    "performance_score": 3600,
                    "ecc_support": False
                },
                "ddr4_ecc": {
                    "name": "DDR4 ECC",
                    "performance_score": 2666,
                    "ecc_support": True
                },
                "ddr5_4800": {
                    "name": "DDR5-4800",
                    "performance_score": 4800,
                    "ecc_support": False
                },
                "ddr5_5600": {
                    "name": "DDR5-5600",
                    "performance_score": 5600,
                    "ecc_support": False
                },
                "ddr5_ecc": {
                    "name": "DDR5 ECC",
                    "performance_score": 4800,
                    "ecc_support": True
                }
            },
            "storage": {
                "sata_hdd": {
                    "name": "SATA HDD",
                    "read_speed": 150,  # MB/s
                    "write_speed": 150,  # MB/s
                    "iops": 100,
                    "reliability_score": 3,
                    "cost_per_gb": 0.02,
                    "suitable_for": ["archival", "bulk_storage"]
                },
                "sata_ssd": {
                    "name": "SATA SSD",
                    "read_speed": 550,  # MB/s
                    "write_speed": 520,  # MB/s
                    "iops": 90000,
                    "reliability_score": 4,
                    "cost_per_gb": 0.1,
                    "suitable_for": ["os", "vm_storage", "databases"]
                },
                "nvme_gen3": {
                    "name": "NVMe Gen3",
                    "read_speed": 3500,  # MB/s
                    "write_speed": 3000,  # MB/s
                    "iops": 500000,
                    "reliability_score": 4.5,
                    "cost_per_gb": 0.15,
                    "suitable_for": ["os", "vm_storage", "databases", "high_performance"]
                },
                "nvme_gen4": {
                    "name": "NVMe Gen4",
                    "read_speed": 7000,  # MB/s
                    "write_speed": 5500,  # MB/s
                    "iops": 1000000,
                    "reliability_score": 4.5,
                    "cost_per_gb": 0.2,
                    "suitable_for": ["os", "vm_storage", "databases", "high_performance"]
                },
                "enterprise_sas": {
                    "name": "Enterprise SAS",
                    "read_speed": 250,  # MB/s
                    "write_speed": 250,  # MB/s
                    "iops": 200,
                    "reliability_score": 4.5,
                    "cost_per_gb": 0.04,
                    "suitable_for": ["archival", "bulk_storage", "enterprise"]
                }
            },
            "network": {
                "gigabit": {
                    "name": "Gigabit Ethernet",
                    "speed": 1000,  # Mbps
                    "suitable_for": ["home_lab", "small_office"]
                },
                "2.5gbe": {
                    "name": "2.5 Gigabit Ethernet",
                    "speed": 2500,  # Mbps
                    "suitable_for": ["home_lab", "small_office", "medium_office"]
                },
                "10gbe": {
                    "name": "10 Gigabit Ethernet",
                    "speed": 10000,  # Mbps
                    "suitable_for": ["medium_office", "large_office", "data_center"]
                },
                "25gbe": {
                    "name": "25 Gigabit Ethernet",
                    "speed": 25000,  # Mbps
                    "suitable_for": ["large_office", "data_center"]
                },
                "40gbe": {
                    "name": "40 Gigabit Ethernet",
                    "speed": 40000,  # Mbps
                    "suitable_for": ["data_center"]
                }
            }
        }
        
        with open(self.hardware_db_path, 'w') as f:
            json.dump(hardware_db, f, indent=2)
    
    def _initialize_vm_profiles(self):
        """Initialize VM profiles with default values."""
        vm_profiles = {
            "minimal": {
                "name": "Minimal Server",
                "description": "Basic server for lightweight services",
                "cpu_cores": 1,
                "memory_mb": 512,
                "disk_gb": 8,
                "network_bandwidth_mbps": 100,
                "suitable_for": ["web_server_small", "dns_server", "dhcp_server"],
                "growth_factor": 1.1
            },
            "small": {
                "name": "Small Server",
                "description": "Small server for basic services",
                "cpu_cores": 2,
                "memory_mb": 2048,
                "disk_gb": 20,
                "network_bandwidth_mbps": 200,
                "suitable_for": ["web_server", "file_server_small", "mail_server_small"],
                "growth_factor": 1.2
            },
            "medium": {
                "name": "Medium Server",
                "description": "Medium-sized server for standard services",
                "cpu_cores": 4,
                "memory_mb": 4096,
                "disk_gb": 50,
                "network_bandwidth_mbps": 500,
                "suitable_for": ["database_server_small", "file_server", "mail_server"],
                "growth_factor": 1.3
            },
            "large": {
                "name": "Large Server",
                "description": "Large server for demanding services",
                "cpu_cores": 8,
                "memory_mb": 16384,
                "disk_gb": 100,
                "network_bandwidth_mbps": 1000,
                "suitable_for": ["database_server", "application_server", "media_server"],
                "growth_factor": 1.4
            },
            "extra_large": {
                "name": "Extra Large Server",
                "description": "Extra large server for resource-intensive services",
                "cpu_cores": 16,
                "memory_mb": 32768,
                "disk_gb": 500,
                "network_bandwidth_mbps": 10000,
                "suitable_for": ["database_server_large", "application_server_large", "ai_workload"],
                "growth_factor": 1.5
            },
            "desktop": {
                "name": "Virtual Desktop",
                "description": "Virtual desktop for remote work",
                "cpu_cores": 4,
                "memory_mb": 8192,
                "disk_gb": 50,
                "network_bandwidth_mbps": 500,
                "suitable_for": ["remote_desktop", "development_workstation"],
                "growth_factor": 1.3
            },
            "gaming": {
                "name": "Gaming VM",
                "description": "VM optimized for gaming with GPU passthrough",
                "cpu_cores": 8,
                "memory_mb": 16384,
                "disk_gb": 250,
                "network_bandwidth_mbps": 1000,
                "gpu_required": True,
                "suitable_for": ["gaming"],
                "growth_factor": 1.4
            }
        }
        
        with open(self.vm_profiles_path, 'w') as f:
            json.dump(vm_profiles, f, indent=2)
    
    def calculate_resources(self, vm_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate required resources based on a VM plan.
        
        Args:
            vm_plan: List of VMs with their profiles and quantities
            
        Returns:
            Dict with calculated resource requirements
        """
        # Load VM profiles
        with open(self.vm_profiles_path, 'r') as f:
            vm_profiles = json.load(f)
        
        # Initialize resource totals
        total_cpu_cores = 0
        total_memory_mb = 0
        total_disk_gb = 0
        total_network_bandwidth_mbps = 0
        gpu_required = False
        
        # Calculate totals
        for vm_item in vm_plan:
            profile_id = vm_item.get("profile_id")
            quantity = vm_item.get("quantity", 1)
            
            if profile_id in vm_profiles:
                profile = vm_profiles[profile_id]
                total_cpu_cores += profile["cpu_cores"] * quantity
                total_memory_mb += profile["memory_mb"] * quantity
                total_disk_gb += profile["disk_gb"] * quantity
                total_network_bandwidth_mbps += profile["network_bandwidth_mbps"] * quantity
                
                if profile.get("gpu_required", False):
                    gpu_required = True
        
        # Add overhead for Proxmox itself (10% for CPU and memory)
        proxmox_cpu_overhead = math.ceil(total_cpu_cores * 0.1)
        proxmox_memory_overhead_mb = math.ceil(total_memory_mb * 0.1)
        
        # Calculate recommended resources with 20% headroom for growth
        recommended_cpu_cores = math.ceil((total_cpu_cores + proxmox_cpu_overhead) * 1.2)
        recommended_memory_mb = math.ceil((total_memory_mb + proxmox_memory_overhead_mb) * 1.2)
        recommended_disk_gb = math.ceil(total_disk_gb * 1.3)  # 30% extra for snapshots and growth
        
        return {
            "required": {
                "cpu_cores": total_cpu_cores + proxmox_cpu_overhead,
                "memory_mb": total_memory_mb + proxmox_memory_overhead_mb,
                "disk_gb": total_disk_gb,
                "network_bandwidth_mbps": total_network_bandwidth_mbps,
                "gpu_required": gpu_required
            },
            "recommended": {
                "cpu_cores": recommended_cpu_cores,
                "memory_mb": recommended_memory_mb,
                "disk_gb": recommended_disk_gb,
                "network_bandwidth_mbps": math.ceil(total_network_bandwidth_mbps * 1.5)  # 50% extra for network
            }
        }
    
    def forecast_disk_usage(self, vm_plan: List[Dict[str, Any]], months: int = 12) -> Dict[str, Any]:
        """
        Forecast disk usage over time based on VM plan.
        
        Args:
            vm_plan: List of VMs with their profiles and quantities
            months: Number of months to forecast
            
        Returns:
            Dict with forecasted disk usage
        """
        # Load VM profiles
        with open(self.vm_profiles_path, 'r') as f:
            vm_profiles = json.load(f)
        
        # Calculate initial disk usage
        initial_disk_gb = 0
        growth_factors = []
        
        for vm_item in vm_plan:
            profile_id = vm_item.get("profile_id")
            quantity = vm_item.get("quantity", 1)
            custom_growth = vm_item.get("growth_factor")
            
            if profile_id in vm_profiles:
                profile = vm_profiles[profile_id]
                initial_disk_gb += profile["disk_gb"] * quantity
                
                # Use custom growth factor if provided, otherwise use profile default
                growth_factor = custom_growth if custom_growth else profile.get("growth_factor", 1.2)
                
                for _ in range(quantity):
                    growth_factors.append(growth_factor)
        
        # Calculate average growth factor
        avg_growth_factor = sum(growth_factors) / len(growth_factors) if growth_factors else 1.2
        
        # Generate forecast
        forecast = []
        current_date = datetime.now()
        current_disk_gb = initial_disk_gb
        
        for month in range(months + 1):
            forecast_date = (current_date + timedelta(days=30 * month)).strftime("%Y-%m")
            
            if month == 0:
                # Initial month
                forecast.append({
                    "date": forecast_date,
                    "disk_gb": current_disk_gb
                })
            else:
                # Apply growth factor
                current_disk_gb = math.ceil(current_disk_gb * (1 + (avg_growth_factor - 1) / 12))
                forecast.append({
                    "date": forecast_date,
                    "disk_gb": current_disk_gb
                })
        
        return {
            "initial_disk_gb": initial_disk_gb,
            "forecast": forecast,
            "avg_growth_factor_annual": avg_growth_factor
        }
    
    def recommend_hardware(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend hardware based on calculated resource requirements.
        
        Args:
            requirements: Dict with resource requirements
            
        Returns:
            Dict with hardware recommendations
        """
        # Load hardware database
        with open(self.hardware_db_path, 'r') as f:
            hardware_db = json.load(f)
        
        # Extract requirements
        required_cpu_cores = requirements["required"]["cpu_cores"]
        recommended_cpu_cores = requirements["recommended"]["cpu_cores"]
        required_memory_mb = requirements["required"]["memory_mb"]
        recommended_memory_mb = requirements["recommended"]["memory_mb"]
        required_disk_gb = requirements["required"]["disk_gb"]
        recommended_disk_gb = requirements["recommended"]["disk_gb"]
        network_bandwidth_mbps = requirements["recommended"]["network_bandwidth_mbps"]
        gpu_required = requirements["required"].get("gpu_required", False)
        
        # Determine environment scale
        if recommended_cpu_cores <= 4 and recommended_memory_mb <= 16384:
            environment = "home_lab"
        elif recommended_cpu_cores <= 16 and recommended_memory_mb <= 65536:
            environment = "small_office"
        elif recommended_cpu_cores <= 64 and recommended_memory_mb <= 262144:
            environment = "medium_office"
        else:
            environment = "large_office"
        
        # Recommend CPU
        cpu_recommendations = []
        for cpu_id, cpu_info in hardware_db["cpu"].items():
            total_threads = cpu_info["cores_per_socket"] * cpu_info["threads_per_core"]
            
            # Check if CPU is suitable for the environment
            if environment in cpu_info["suitable_for"] and cpu_info["virtualization_support"]:
                # Calculate how many CPUs would be needed
                cpus_needed = math.ceil(recommended_cpu_cores / total_threads)
                
                if cpus_needed <= 2:  # Limit to dual-socket configurations
                    cpu_recommendations.append({
                        "id": cpu_id,
                        "name": cpu_info["name"],
                        "quantity": cpus_needed,
                        "total_cores": cpu_info["cores_per_socket"] * cpus_needed,
                        "total_threads": total_threads * cpus_needed,
                        "performance_score": cpu_info["performance_score"] * cpus_needed
                    })
        
        # Sort CPU recommendations by performance score
        cpu_recommendations.sort(key=lambda x: x["performance_score"], reverse=True)
        
        # Recommend memory
        memory_size_gb = math.ceil(recommended_memory_mb / 1024)
        memory_recommendations = []
        
        # Determine suitable memory types
        for memory_id, memory_info in hardware_db["memory"].items():
            # For servers, prefer ECC memory
            if environment in ["medium_office", "large_office", "data_center"] and not memory_info["ecc_support"]:
                continue
            
            memory_recommendations.append({
                "id": memory_id,
                "name": memory_info["name"],
                "size_gb": memory_size_gb,
                "performance_score": memory_info["performance_score"]
            })
        
        # Sort memory recommendations by performance score
        memory_recommendations.sort(key=lambda x: x["performance_score"], reverse=True)
        
        # Recommend storage
        storage_recommendations = []
        
        # Determine storage tiers based on requirements
        os_storage_gb = min(100, recommended_disk_gb * 0.1)  # 10% for OS, max 100GB
        vm_storage_gb = recommended_disk_gb - os_storage_gb
        
        # OS storage recommendations
        for storage_id, storage_info in hardware_db["storage"].items():
            if "os" in storage_info["suitable_for"]:
                storage_recommendations.append({
                    "id": storage_id,
                    "name": storage_info["name"],
                    "purpose": "OS and Proxmox",
                    "size_gb": math.ceil(os_storage_gb),
                    "read_speed": storage_info["read_speed"],
                    "write_speed": storage_info["write_speed"],
                    "iops": storage_info["iops"]
                })
        
        # VM storage recommendations
        for storage_id, storage_info in hardware_db["storage"].items():
            if "vm_storage" in storage_info["suitable_for"]:
                storage_recommendations.append({
                    "id": storage_id,
                    "name": storage_info["name"],
                    "purpose": "VM Storage",
                    "size_gb": math.ceil(vm_storage_gb),
                    "read_speed": storage_info["read_speed"],
                    "write_speed": storage_info["write_speed"],
                    "iops": storage_info["iops"]
                })
        
        # Sort storage recommendations by IOPS for each purpose
        os_storage = sorted([s for s in storage_recommendations if s["purpose"] == "OS and Proxmox"], 
                           key=lambda x: x["iops"], reverse=True)
        vm_storage = sorted([s for s in storage_recommendations if s["purpose"] == "VM Storage"], 
                           key=lambda x: x["iops"], reverse=True)
        
        # Recommend network
        network_recommendations = []
        
        for network_id, network_info in hardware_db["network"].items():
            if environment in network_info["suitable_for"] and network_info["speed"] >= network_bandwidth_mbps:
                network_recommendations.append({
                    "id": network_id,
                    "name": network_info["name"],
                    "speed_mbps": network_info["speed"]
                })
        
        # Sort network recommendations by speed
        network_recommendations.sort(key=lambda x: x["speed_mbps"])
        
        # Take top recommendations
        top_cpu = cpu_recommendations[:3] if cpu_recommendations else []
        top_memory = memory_recommendations[:2] if memory_recommendations else []
        top_os_storage = os_storage[:2] if os_storage else []
        top_vm_storage = vm_storage[:2] if vm_storage else []
        top_network = network_recommendations[:2] if network_recommendations else []
        
        return {
            "environment_scale": environment,
            "cpu": top_cpu,
            "memory": top_memory,
            "storage": {
                "os": top_os_storage,
                "vm": top_vm_storage
            },
            "network": top_network,
            "gpu_required": gpu_required
        }
    
    def save_resource_plan(self, plan: Dict[str, Any]) -> str:
        """
        Save a resource plan to disk.
        
        Args:
            plan: Resource plan data
            
        Returns:
            Plan ID
        """
        # Generate plan ID if not provided
        if "id" not in plan:
            plan["id"] = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Add timestamps
        if "created_at" not in plan:
            plan["created_at"] = datetime.now().isoformat()
        
        plan["updated_at"] = datetime.now().isoformat()
        
        # Save plan to disk
        plan_path = os.path.join(self.plans_dir, f"{plan['id']}.json")
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)
        
        return plan["id"]
    
    def get_resource_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a resource plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Resource plan or None if not found
        """
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        
        if not os.path.exists(plan_path):
            return None
        
        with open(plan_path, 'r') as f:
            return json.load(f)
    
    def get_resource_plans(self) -> List[Dict[str, Any]]:
        """
        Get all resource plans.
        
        Returns:
            List of resource plans
        """
        plans = []
        
        for filename in os.listdir(self.plans_dir):
            if filename.endswith(".json"):
                plan_path = os.path.join(self.plans_dir, filename)
                
                with open(plan_path, 'r') as f:
                    plan = json.load(f)
                    plans.append(plan)
        
        # Sort by updated_at (newest first)
        plans.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return plans
    
    def delete_resource_plan(self, plan_id: str) -> bool:
        """
        Delete a resource plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            True if deleted, False if not found
        """
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        
        if not os.path.exists(plan_path):
            return False
        
        os.remove(plan_path)
        return True
    
    def get_vm_profiles(self) -> Dict[str, Any]:
        """
        Get all VM profiles.
        
        Returns:
            Dict of VM profiles
        """
        with open(self.vm_profiles_path, 'r') as f:
            return json.load(f)
    
    def get_hardware_database(self) -> Dict[str, Any]:
        """
        Get the hardware database.
        
        Returns:
            Dict with hardware database
        """
        with open(self.hardware_db_path, 'r') as f:
            return json.load(f)


# Initialize service instance
resource_planning_service = ResourcePlanningService()
