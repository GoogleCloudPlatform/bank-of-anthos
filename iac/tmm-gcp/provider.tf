provider "google" {
  project = "tmm-fcs-444213"
}

terraform {
	required_providers {
		google = {
	    version = "~> 6.13.0"
		}
  }
}
