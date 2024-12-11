resource "google_container_cluster" "tfer--bc-1" {
  addons_config {
    dns_cache_config {
      enabled = "false"
    }

    gce_persistent_disk_csi_driver_config {
      enabled = "true"
    }

    gcs_fuse_csi_driver_config {
      enabled = "false"
    }

    horizontal_pod_autoscaling {
      disabled = "false"
    }

    http_load_balancing {
      disabled = "false"
    }

    network_policy_config {
      disabled = "true"
    }

    ray_operator_config {
      enabled = "false"
    }
  }

  binary_authorization {
    enabled         = "false"
    evaluation_mode = "DISABLED"
  }

  cluster_autoscaling {
    autoscaling_profile = "BALANCED"
    enabled             = "false"
  }

  cluster_ipv4_cidr = "10.68.0.0/14"

  control_plane_endpoints_config {
    dns_endpoint_config {
      allow_external_traffic = "false"
      endpoint               = "gke-440ac31f693e4c218aba375e1c7eaa351213-493729294920.us-central1-c.gke.goog"
    }
  }

  database_encryption {
    state = "DECRYPTED"
  }

  datapath_provider         = "LEGACY_DATAPATH"
  default_max_pods_per_node = "110"

  default_snat_status {
    disabled = "false"
  }

  description                              = "cluster for tmm-fcs"
  enable_autopilot                         = "false"
  enable_cilium_clusterwide_network_policy = "false"
  enable_intranode_visibility              = "false"
  enable_kubernetes_alpha                  = "false"
  enable_l4_ilb_subsetting                 = "false"
  enable_legacy_abac                       = "false"
  enable_multi_networking                  = "false"
  enable_shielded_nodes                    = "true"
  enable_tpu                               = "false"

  enterprise_config {
    desired_tier = "STANDARD"
  }

  initial_node_count = "0"

  ip_allocation_policy {
    cluster_ipv4_cidr_block = "10.68.0.0/14"

    pod_cidr_overprovision_config {
      disabled = "false"
    }

    services_ipv4_cidr_block = "34.118.224.0/20"
    stack_type               = "IPV4"
  }

  location = "us-central1-c"

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  logging_service = "logging.googleapis.com/kubernetes"

  master_auth {
    client_certificate_config {
      issue_client_certificate = "false"
    }
  }

  monitoring_config {
    advanced_datapath_observability_config {
      enable_metrics = "false"
      enable_relay   = "false"
    }

    enable_components = ["CADVISOR", "DAEMONSET", "DEPLOYMENT", "HPA", "KUBELET", "POD", "STATEFULSET", "STORAGE", "SYSTEM_COMPONENTS"]

    managed_prometheus {
      enabled = "true"
    }
  }

  monitoring_service = "monitoring.googleapis.com/kubernetes"
  name               = "bc-1"
  network            = "projects/tmm-fcs-444213/global/networks/default"

  network_policy {
    enabled  = "false"
    provider = "PROVIDER_UNSPECIFIED"
  }

  networking_mode = "VPC_NATIVE"

  node_pool_defaults {
    node_config_defaults {
      insecure_kubelet_readonly_port_enabled = "FALSE"
      logging_variant                        = "DEFAULT"
    }
  }

  node_version = "1.30.5-gke.1699000"

  notification_config {
    pubsub {
      enabled = "false"
    }
  }

  private_cluster_config {
    enable_private_endpoint = "false"
    enable_private_nodes    = "false"

    master_global_access_config {
      enabled = "false"
    }
  }

  project = "tmm-fcs-444213"

  release_channel {
    channel = "REGULAR"
  }

  secret_manager_config {
    enabled = "false"
  }

  security_posture_config {
    mode               = "BASIC"
    vulnerability_mode = "VULNERABILITY_DISABLED"
  }

  service_external_ips_config {
    enabled = "false"
  }

  subnetwork = "projects/tmm-fcs-444213/regions/us-central1/subnetworks/default"
}
