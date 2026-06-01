# AWS IoT Core Setup Guide

This guide explains how to connect this project to a **real** AWS IoT Core endpoint.
The project works out-of-the-box in **dry-run mode** (no AWS account needed).

---

## 1. Create an AWS IoT Thing

1. Log in to the [AWS Console](https://console.aws.amazon.com/iot/).
2. Navigate to **IoT Core → Manage → Things → Create things**.
3. Name your thing: `smart-factory-edge-01`.
4. Select **Auto-generate a new certificate**.
5. Attach the policy below and download all certificate files.

---

## 2. Create an IoT Policy

In **IoT Core → Security → Policies → Create policy**, paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 3. Place Certificate Files

Copy your downloaded certificates into `config/certs/`:

```
config/certs/
├── AmazonRootCA1.pem
├── device-certificate.pem.crt
└── private.pem.key
```

> ⚠️ These files are in `.gitignore` — never commit real credentials.

---

## 4. Update mqtt_publisher.py

Set your endpoint (found in **IoT Core → Settings**):

```python
ENDPOINT = "YOUR_ID.iot.ap-south-1.amazonaws.com"
DRY_RUN  = False
```

---

## 5. Install the AWS IoT SDK

```bash
pip install awsiotsdk
```

---

## 6. IoT Rule (optional — route to Lambda)

To trigger `fault_detector.py` automatically via AWS Lambda:

1. Go to **IoT Core → Message routing → Rules → Create rule**.
2. SQL: `SELECT * FROM 'factory/conveyor/#' WHERE severity <> 'normal'`
3. Action: **Lambda function** → point to your deployed `fault_detector` Lambda.
