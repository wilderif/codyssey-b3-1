## 배포와 검증

```bash
terraform -chdir=infra init
terraform -chdir=infra fmt -check
terraform -chdir=infra validate
bash -n infra/user_data.sh
terraform -chdir=infra plan -var-file=local.tfvars -out=apply.tfplan
# Review the plan before applying.
terraform -chdir=infra apply apply.tfplan
terraform -chdir=infra output
```

실행 결과 발췌:

```text
Success! The configuration is valid.
Plan: 8 to add, 0 to change, 0 to destroy.
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
```

SSH로 접속해 초기화 완료와 서비스를 확인한다.

```bash
public_ip=$(terraform -chdir=infra output -raw public_ip)
ssh -i "$HOME/.ssh/codyssey-assignment" "ubuntu@$public_ip"
sudo cloud-init status --wait
sudo systemctl is-enabled nginx
sudo systemctl is-active nginx
sudo nginx -t
curl --include --fail http://localhost/
curl --head --fail https://example.com
exit
curl --include --fail --show-error --max-time 10 "http://$public_ip/health"
```

| 검증 | 확인 결과 |
| --- | --- |
| 네트워크 | subnet의 IGW 기본 경로 `active`, public IPv4 할당 |
| 보안 그룹 | HTTP 80 공개, SSH 22 개인 IPv4 `/32` 제한 |
| 인스턴스 | 상태 검사 `ok`, EBS·IMDSv2·CPU credit 설정 일치 |
| SSH / 초기화 | 전용 키 접속 성공, cloud-init `done` |
| Nginx | `enabled`, `active`, 설정 검사 성공 |
| 내부 / 아웃바운드 | localhost와 `https://example.com` 모두 HTTP 200 |
| 외부 접속 | `/health`: HTTP 200·`OK`, 브라우저 `/`: `Hello Cloud` |

외부 접속 증빙은 **방식 B**다. 아래는 실제 출력에서 날짜·부가 헤더를 생략하고 주소를 마스킹한 결과다.

```text
$ curl --include --fail --silent --show-error --max-time 10 http://masked-public-ip/health
HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: 2

OK
```
