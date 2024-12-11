output "google_container_cluster_tfer--bc-1_self_link" {
  value = "${google_container_cluster.tfer--bc-1.self_link}"
}

output "google_container_node_pool_tfer--bc-1_default-pool_id" {
  value = "${google_container_node_pool.tfer--bc-1_default-pool.id}"
}
