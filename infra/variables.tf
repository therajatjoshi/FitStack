variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = "7ec7c4d6-8b6b-4bf2-ab4c-9086a21a8a0c"
}

variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
  default     = "fitstack"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "centralindia"
}

variable "docker_image_name" {
  description = "Docker image name and tag to run on the Web App (pushed to ACR after deploy)"
  type        = string
  default     = "fitstack-backend:latest"
}
