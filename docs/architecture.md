## 구성

```mermaid
flowchart TB
    client["외부 클라이언트"]
    subgraph vpc["VPC · 10.0.0.0/16"]
        igw["Internet Gateway"]
        route["Route Table<br/>0.0.0.0/0 → IGW"]
        subgraph subnet["Public Subnet · 10.0.1.0/24"]
            sg["Security Group<br/>HTTP 80: 0.0.0.0/0<br/>SSH 22: 개인 IPv4 /32"]
            ec2["EC2 · Nginx<br/>Public IP: masked-public-ip<br/>/ · /health"]
            sg --> ec2
        end
        igw --> route
        route --> sg
    end
    client -->|"HTTP / 제한된 SSH"| igw
    ec2 -.->|"인터넷 아웃바운드"| igw
```

| 항목 | 설정 |
| --- | --- |
| 리전 / EC2 | `ap-northeast-2` / `t3.micro` |
| AMI | Canonical Ubuntu 24.04 LTS `x86_64`, 소유자·아키텍처 확인 |
| EBS | 암호화된 `gp3` 8 GiB, 인스턴스 종료 시 삭제 |
| 인스턴스 | 자동 public IPv4, IMDSv2 필수, CPU credit `standard` |
| 아웃바운드 | 전체 IPv4 허용 |

접속 IP와 리소스 ID는 마스킹했다. 네트워크 CIDR은 구성값이다.
