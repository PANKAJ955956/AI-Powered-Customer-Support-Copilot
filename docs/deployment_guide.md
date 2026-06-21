# AWS Production Deployment Guide

This guide describes how to deploy the AI Customer Support Copilot CRM onto AWS.

---

## 1. Setup AWS S3 Bucket (Knowledge Documents)
To support persistent company document storage:
1. Open the **AWS S3 Console** and click **Create Bucket**.
2. Name the bucket (e.g. `copilot-knowledgebase-prod`) and choose your region.
3. Configure the bucket policy to allow secure access from your EC2 Instance role.

**IAM S3 Access Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::copilot-knowledgebase-prod",
        "arn:aws:s3:::copilot-knowledgebase-prod/*"
      ]
    }
  ]
}
```

---

## 2. Provision AWS EC2 Instance
1. Launch a `t3.medium` (or larger) instance using the **Ubuntu Server 22.04 LTS** AMI.
2. Configure **Security Groups**:
   - Inbound HTTP (Port 80) & HTTPS (Port 443) -> Open to Public
   - Inbound SSH (Port 22) -> Restrict to your IP
   - Inbound FastAPI (Port 8000) -> Internal access or proxy only
3. Create and download your SSH Key Pair (`copilot-key.pem`).

---

## 3. Configure EC2 Server Environment
SSH into your instance:
```bash
ssh -i "copilot-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com
```

Update packages and install Docker:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 4. Deploy Application
1. **Clone project source** to the EC2 server:
   ```bash
   git clone <repository_url> copilot-crm
   cd copilot-crm
   ```
2. **Create production configuration**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Modify the `DATABASE_URL` to point to your secure PostgreSQL service, insert your production `OPENAI_API_KEY`, and change the `JWT_SECRET` key.*

3. **Launch Docker Compose services**:
   ```bash
   sudo docker-compose -f docker-compose.yml up -d --build
   ```

---

## 5. Reverse Proxy Setup (Nginx)
Configure Nginx on the EC2 host to manage SSL certificates and forward traffic:
```bash
sudo apt-get install -y nginx
sudo nano /etc/nginx/sites-available/default
```

Replace the content with the following configuration:
```nginx
server {
    listen 80;
    server_name copilot.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000; # Next.js frontend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000; # FastAPI backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Restart Nginx:
```bash
sudo systemctl restart nginx
```

Use **Certbot** to automatically provision Let's Encrypt SSL certificates:
```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d copilot.yourdomain.com
```
