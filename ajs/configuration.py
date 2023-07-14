configuration_type = "jenkins"  # Change this variable to switch configurations

if configuration_type == "legacy":
    from legacy_configuration import Config
elif configuration_type == "jenkins":
    from jenkins_configuration import Config
