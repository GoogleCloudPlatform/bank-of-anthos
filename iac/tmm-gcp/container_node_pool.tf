resource "google_container_node_pool" "tfer--bc-1_default-pool" {
  cluster            = "${google_container_cluster.tfer--bc-1.name}"
  initial_node_count = "3"
  location           = "us-central1-c"

  management {
    auto_repair  = "true"
    auto_upgrade = "true"
  }

  max_pods_per_node = "110"
  name              = "default-pool"

  network_config {
    create_pod_range     = "false"
    enable_private_nodes = "false"
    pod_ipv4_cidr_block  = "10.68.0.0/14"
    pod_range            = "gke-bc-1-pods-440ac31f"
  }

  node_config {
    advanced_machine_features {
      enable_nested_virtualization = "false"
      threads_per_core             = "0"
    }

    disk_size_gb                = "100"
    disk_type                   = "pd-balanced"
    enable_confidential_storage = "false"
    image_type                  = "COS_CONTAINERD"
    local_ssd_count             = "0"
    logging_variant             = "DEFAULT"
    machine_type                = "e2-standard-2"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes    = ["https://www.googleapis.com/auth/devstorage.read_only", "https://www.googleapis.com/auth/logging.write", "https://www.googleapis.com/auth/monitoring", "https://www.googleapis.com/auth/service.management.readonly", "https://www.googleapis.com/auth/servicecontrol", "https://www.googleapis.com/auth/trace.append"]
    preemptible     = "false"
    service_account = "default"

    shielded_instance_config {
      enable_integrity_monitoring = "true"
      enable_secure_boot          = "false"
    }

    spot = "false"
  }

  node_count     = "3"
  node_locations = ["us-central1-c"]
  project        = "tmm-fcs-444213"

  queued_provisioning {
    enabled = "false"
  }

  upgrade_settings {
    max_surge       = "1"
    max_unavailable = "0"
    strategy        = "SURGE"
  }

  version = "1.30.5-gke.1699000"
}
