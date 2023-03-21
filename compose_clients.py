import sys

client_number = sys.argv[1]

if not client_number.isdigit():
    print("input not a number")
    sys.exit(1)

if int(client_number) < 1:
    print("must be 1 client or more")
    sys.exit(1)

save = []
middle = 0
with open("docker-compose-dev.yaml", "r") as docker_compose:
    contents = docker_compose.readlines()
    
    for line in contents:
        if "client1:" in line:
            break
        save.append(line)
    
    middle = len(save)

    for i, line in enumerate(contents):
        if line[:9] == "networks:":
            save = save + contents[i:]
            break

with open("docker-compose-dev.yaml", "w") as docker_compose:
    for line in save[:middle]:
        docker_compose.write(line)

    for i in range(int(client_number)):
        docker_compose.write(f"  client{i+1}:\n")
        docker_compose.write(f"    container_name: client{i+1}\n")
        docker_compose.write("    image: client:latest\n")
        docker_compose.write("    entrypoint: /client\n")
        docker_compose.write("    environment:\n")
        docker_compose.write(f"      - CLI_ID={i+1}\n")
        docker_compose.write("      - CLI_LOG_LEVEL=DEBUG\n")
        docker_compose.write("    networks:\n")
        docker_compose.write("      - testing_net\n")
        docker_compose.write("    depends_on:\n")
        docker_compose.write("      - server\n")
        docker_compose.write("    volumes:\n")
        docker_compose.write("      - ./client/config.yaml:/config.yaml\n")
        docker_compose.write("\n")

    for line in save[middle:]:
        docker_compose.write(line)
