---
description: 'How to configure your Giskard application: Email notifications and API tokens'
---

# Configuration

## Change the LIME parameters

To compute local explanations of textual features, Giskard uses the LIME algorithm. LIME creates `n_samples` of distorted texts to compute the explanation. When `n_samples` is high, the provided explanation is better, but the computation time will be higher as well.

By default, n\_samples is equal to 500. To change it, you need to change the project settings. To do that, click on **Edit** in the top right corner of your screen (see the image below)

<figure><img src="../.gitbook/assets/image (3) (1).png" alt=""><figcaption></figcaption></figure>

## Email notifications

Giskard can send email notifications about different events like inspector feedbacks or user invitation to the platform.

To configure this feature SMTP server credentials should be provided at startup through environment variables

| Environment variable name | Purpose                                 |
| ------------------------- | --------------------------------------- |
| GISKARD\_MAIL\_HOST       | SMTP server address                     |
| GISKARD\_MAIL\_PORT       | SMTP port, 587 by default               |
| GISKARD\_MAIL\_USERNAME   |                                         |
| GISKARD\_MAIL\_PASSWORD   |                                         |
| GISKARD\_MAIL\_BASEURL    | Publicly available Giskard instance URL |

## Backend JWT secret. Persistent user sessions.

Giskard authentication is based on [JWT tokens](https://jwt.io/). These tokens are issued by Giskard backend based on a JWT secret key.

To reinforce security there's no default value of the secret key, whenever the backend starts it generates one automatically. However it means that users' sessions are invalidated and they have to re-login.&#x20;

For production instances, it's preferred to keep user sessions alive no matter whether the server was rebooted or not. In this case, the JWT secret can be set from the outside by specifying `GISKARD_JWT_SECRET` environment variable. Its value should contain a base64 encoded bytes sequence of at least 128 bytes.

The following script can generate and store a secret key of 256 bytes:

```bash
# for zsh
echo export GISKARD_JWT_SECRET=`openssl rand -base64 256 | tr -d '\n'` >> ~/.zshrc

# for bash
echo export GISKARD_JWT_SECRET=`openssl rand -base64 256 | tr -d '\n'` >> ~/.bashrc
```

## Troubleshooting[​](https://docs.airbyte.com/deploying-airbyte/on-aws-ec2#troubleshooting)

If you encounter any issues, join our [**Discord**](https://discord.gg/fkv7CAr3FE) on our #support channel. Our community will help!&#x20;

## [​](https://docs.airbyte.com/deploying-airbyte/on-aws-ec2#troubleshooting)
