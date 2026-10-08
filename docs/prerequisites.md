## 준비

- Terraform `>= 1.15, < 2.0`, AWS CLI, OpenSSH, curl을 설치한다. AWS provider는 `~> 6.0`을 사용한다.
- 비루트 운영자가 실습용 IAM 사용자를 준비한다. EC2·VPC·SG·key pair 관리에 필요한 권한만 부여하고 리전·리소스·태그로 범위를 제한한다.
- EC2·EBS·public IPv4의 계정별 무료 범위 또는 크레딧을 확인한다.

아래 명령은 저장소 루트에서 실행한다. 프로필 이름은 예시이며, SSH 키는 없을 때만 생성한다.

```bash
aws configure --profile codyssey-assignment
aws sts get-caller-identity --profile codyssey-assignment --region ap-northeast-2
ssh-keygen -t ed25519 -f "$HOME/.ssh/codyssey-assignment" -C codyssey-b3-1
chmod 600 "$HOME/.ssh/codyssey-assignment"
curl -4 --fail --silent --show-error https://checkip.amazonaws.com
cp -n infra/example.tfvars infra/local.tfvars
```

`infra/local.tfvars`에 `aws_profile`, 개인 공인 IPv4의 `ssh_allowed_cidr`(`/32`), 전용 `public_key_path`를 입력한다. 공인 IP가 바뀌면 SSH 허용 주소도 갱신한다.
