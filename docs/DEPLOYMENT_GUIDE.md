# AMTD Deployment Guide

**Version:** 1.0  
**Last Updated:** November 26, 2025

---

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Manual Deployment](#manual-deployment)
- [Production Hardening](#production-hardening)
- [Monitoring Setup](#monitoring-setup)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

---

## Deployment Options

### Comparison Matrix

| Feature | Docker Compose | Kubernetes | Manual |
|---------|----------------|------------|--------|
| **Complexity** | Low | High | Medium |
| **Scalability** | Limited | Excellent | Manual |
| **HA Support** | No | Yes | Manual |
| **Best For** | Dev/Test/Small Teams | Production/Enterprise | Custom Setups |
| **Setup Time** | 10 minutes | 1-2 hours | 2-4 hours |

---

## Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum
- 50GB disk space

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/amtd.git
cd amtd

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with your settings
nano .env

# 4. Start all services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. View logs
docker-compose logs -f jenkins
```

### Docker Compose Configuration

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts
    container_name: amtd-jenkins
    privileged: true
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - ./config:/var/jenkins_config
    environment:
      JAVA_OPTS: "-Djenkins.install.runSetupWizard=false"
    networks:
      - amtd-network
    restart: unless-stopped
      
  postgres:
    image: postgres:15
    container_name: amtd-postgres
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - amtd-network
    restart: unless-stopped
      
  minio:
    image: minio/minio
    container_name: amtd-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    networks:
      - amtd-network
    restart: unless-stopped
      
  juice-shop:
    image: bkimminich/juice-shop
    container_name: amtd-juice-shop
    ports:
      - "3000:3000"
    networks:
      - amtd-network
    restart: unless-stopped

volumes:
  jenkins_home:
  postgres_data:
  minio_data:

networks:
  amtd-network:
    driver: bridge
```

### Initial Setup

```bash
# Get Jenkins initial password
docker exec amtd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Access Jenkins
open http://localhost:8080

# Configure Jenkins:
# 1. Enter initial password
# 2. Install suggested plugins
# 3. Create admin user
# 4. Configure system settings
```

### Configuration

```bash
# Create config directory
mkdir -p config/applications

# Create first application config
cat > config/applications/juice-shop.yaml <<EOF
application:
  name: "OWASP Juice Shop"
  url: "http://juice-shop:3000"
  owner: "security@example.com"
  scan:
    schedule: "0 2 * * *"
    type: full
EOF

# Restart to apply changes
docker-compose restart jenkins
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- Helm 3.0+ (optional)
- 16GB RAM minimum (cluster)
- 200GB storage

### Namespace Setup

```bash
# Create namespace
kubectl create namespace amtd

# Set as default
kubectl config set-context --current --namespace=amtd
```

### Deploy PostgreSQL

**k8s/postgresql/statefulset.yaml:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: amtd
type: Opaque
stringData:
  password: your-secure-password
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: amtd
spec:
  ports:
  - port: 5432
  selector:
    app: postgres
  clusterIP: None
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: amtd
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: amtd
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POSTGRES_DB
          value: amtd
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
```

### Deploy Jenkins

**k8s/jenkins/deployment.yaml:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jenkins-pvc
  namespace: amtd
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins
  namespace: amtd
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      serviceAccountName: jenkins
      securityContext:
        fsGroup: 1000
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts
        ports:
        - containerPort: 8080
        - containerPort: 50000
        volumeMounts:
        - name: jenkins-home
          mountPath: /var/jenkins_home
        env:
        - name: JAVA_OPTS
          value: "-Djenkins.install.runSetupWizard=false"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: jenkins-home
        persistentVolumeClaim:
          claimName: jenkins-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: jenkins
  namespace: amtd
spec:
  type: LoadBalancer
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  - name: agent
    port: 50000
    targetPort: 50000
  selector:
    app: jenkins
```

### Deploy MinIO

```bash
# Using Helm
helm repo add minio https://charts.min.io/
helm install minio minio/minio \
  --namespace amtd \
  --set rootUser=admin \
  --set rootPassword=your-secure-password \
  --set persistence.size=500Gi
```

### Apply All Resources

```bash
# Deploy everything
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgresql/
kubectl apply -f k8s/jenkins/
kubectl apply -f k8s/minio/

# Check status
kubectl get all -n amtd

# Get external IPs
kubectl get svc -n amtd
```

### Access Services

```bash
# Jenkins
kubectl port-forward svc/jenkins 8080:8080 -n amtd

# MinIO Console
kubectl port-forward svc/minio 9001:9001 -n amtd

# Get Jenkins initial password
kubectl exec -n amtd deployment/jenkins -- \
  cat /var/jenkins_home/secrets/initialAdminPassword
```

---

## Manual Deployment

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Install Jenkins

```bash
# Add Jenkins repository
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | \
  sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# Install
sudo apt-get update
sudo apt-get install jenkins

# Start service
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

### 3. Install PostgreSQL

```bash
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql -c "CREATE DATABASE amtd;"
sudo -u postgres psql -c "CREATE USER amtd WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE amtd TO amtd;"
```

### 4. Configure Jenkins

```bash
# Install required plugins
java -jar jenkins-cli.jar -s http://localhost:8080/ install-plugin \
  docker-workflow \
  pipeline-stage-view \
  html-publisher \
  email-ext \
  git

# Restart Jenkins
sudo systemctl restart jenkins
```

---

## Production Hardening

### Security Checklist

- [ ] Change all default passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable Jenkins CSRF protection
- [ ] Set up user authentication (LDAP/SAML)
- [ ] Implement RBAC
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Secure secret management
- [ ] Network segmentation

### HTTPS Configuration

```bash
# Generate SSL certificate
sudo certbot certonly --standalone -d amtd.example.com

# Configure nginx reverse proxy
sudo apt-get install nginx

cat > /etc/nginx/sites-available/amtd <<EOF
server {
    listen 443 ssl;
    server_name amtd.example.com;

    ssl_certificate /etc/letsencrypt/live/amtd.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/amtd.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/amtd /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'jenkins'
    static_configs:
      - targets: ['jenkins:8080']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
  
  - job_name: 'minio'
    static_configs:
      - targets: ['minio:9000']
```

### Grafana Dashboards

```bash
# Import pre-built dashboards
# Jenkins: ID 9964
# PostgreSQL: ID 9628
# System: ID 1860
```

---

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

# Backup Jenkins
tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz /var/jenkins_home

# Backup PostgreSQL
pg_dump amtd > amtd-db-backup-$(date +%Y%m%d).sql

# Backup MinIO
mc mirror minio/amtd-reports /backups/minio/$(date +%Y%m%d)

# Upload to S3
aws s3 sync /backups s3://amtd-backups/
```

### Recovery Procedure

```bash
# Restore Jenkins
tar -xzf jenkins-backup-YYYYMMDD.tar.gz -C /var/jenkins_home

# Restore PostgreSQL
psql amtd < amtd-db-backup-YYYYMMDD.sql

# Restore MinIO
mc mirror /backups/minio/YYYYMMDD minio/amtd-reports
```

---

## Troubleshooting

### Common Issues

**Jenkins won't start:**
```bash
# Check logs
sudo journalctl -u jenkins -f

# Check Java
java -version

# Increase memory
sudo nano /etc/default/jenkins
# Add: JAVA_ARGS="-Xmx2048m"
```

**Database connection errors:**
```bash
# Test connection
psql -h localhost -U amtd -d amtd

# Check PostgreSQL status
sudo systemctl status postgresql
```

**Docker permission denied:**
```bash
# Add user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

---

**Document Version:** 1.0  
**Last Updated:** November 26, 2025
