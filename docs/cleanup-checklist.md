## 리소스 정리

삭제 계획을 검토한 뒤 `destroy`의 삭제 목록을 확인하고 `yes`로 승인한다.

```bash
terraform -chdir=infra plan -destroy -var-file=local.tfvars
terraform -chdir=infra destroy -var-file=local.tfvars
terraform -chdir=infra state list
```

```text
Plan: 0 to add, 0 to change, 8 to destroy.
Destroy complete! Resources: 8 destroyed.
```

`state list` 출력은 비어 있었다. 실제 AWS 조회에서도 정리를 확인했다.

| 대상 | 정리 결과 |
| --- | --- |
| EC2 `masked-instance-id` | `terminated` |
| EBS `masked-volume-id` | 삭제, 조회 결과 `[]` |
| AWS key pair | 삭제, 조회 결과 `[]` |
| subnet·route table·association·SG·IGW·VPC | 삭제 완료 |
| 기본 route table·SG·NACL·EC2 ENI | 잔여 리소스 없음 |
| Elastic IP·NAT Gateway·ELB/ALB·RDS | 미생성, 서울 조회 목록 `[]` |
| Billing | 조회 완료. 실습 비용은 아직 반영되지 않아 최종 금액 확인 불가 |

### AWS CLI로 정리 확인

실습 프로필과 서울 리전으로 조회한다. 실습 리소스는 `Project=codyssey-b3-1` 태그로 찾는다. EC2는 `terminated` 또는 `[]`, 나머지 생성 리소스는 `[]`인지 확인한다.

```bash
aws_args=(--profile codyssey-assignment --region ap-northeast-2 --output json --no-cli-pager)
project_filter='Name=tag:Project,Values=codyssey-b3-1'

aws ec2 describe-instances "${aws_args[@]}" --filters "$project_filter" --query 'Reservations[].Instances[].[InstanceId,State.Name]'
aws ec2 describe-volumes "${aws_args[@]}" --filters "$project_filter" --query 'Volumes[].VolumeId'
aws ec2 describe-key-pairs "${aws_args[@]}" --filters "$project_filter" --query 'KeyPairs[].KeyName'
aws ec2 describe-subnets "${aws_args[@]}" --filters "$project_filter" --query 'Subnets[].SubnetId'
aws ec2 describe-route-tables "${aws_args[@]}" --filters "$project_filter" --query 'RouteTables[].RouteTableId'
aws ec2 describe-security-groups "${aws_args[@]}" --filters "$project_filter" --query 'SecurityGroups[].GroupId'
aws ec2 describe-internet-gateways "${aws_args[@]}" --filters "$project_filter" --query 'InternetGateways[].InternetGatewayId'
aws ec2 describe-vpcs "${aws_args[@]}" --filters "$project_filter" --query 'Vpcs[].VpcId'
```

미생성 항목은 서울 리전 목록을 확인한다. 목록이 비어 있지 않으면 실습과 관련된 리소스인지 구분한다. NAT Gateway는 `deleted` 상태를 제외한다.

```bash
aws ec2 describe-addresses "${aws_args[@]}" --query 'Addresses[].AllocationId'
aws ec2 describe-nat-gateways "${aws_args[@]}" --query "NatGateways[?State!='deleted'].[NatGatewayId,VpcId,State]"
aws elbv2 describe-load-balancers "${aws_args[@]}" --query 'LoadBalancers[].[LoadBalancerName,VpcId]'
aws elb describe-load-balancers "${aws_args[@]}" --query 'LoadBalancerDescriptions[].[LoadBalancerName,VPCId]'
aws rds describe-db-instances "${aws_args[@]}" --query 'DBInstances[].DBInstanceIdentifier'
aws rds describe-db-clusters "${aws_args[@]}" --query 'DBClusters[].DBClusterIdentifier'
```

조회 권한 오류는 삭제 완료의 근거가 아니다. ELB·RDS 조회 권한이 없으면 권한이 있는 비루트 운영자가 확인한다.
