# Mini Redis

Python 표준 라이브러리만 사용하는 CLI 기반 Mini Redis입니다. 문자열 key-value 저장, 직접 구현한 해시맵, 이중 연결 리스트 기반 LRU, 최소 힙 기반 TTL 만료 관리를 다룹니다.

## 실행 방법

```bash
$ python3 src/main.py
```

```bash
$ uv run python3 src/main.py
```

프롬프트는 `mini-redis>`이며 `exit` 또는 `quit`으로 종료합니다.

## 폴더 구조

```text
.
├── README.md
├── src
│   ├── main.py
│   └── mini_redis
│       ├── cli
│       │   ├── parser.py
│       │   └── repl.py
│       ├── core
│       │   └── store.py
│       └── data_structures
│           ├── doubly_linked_list.py
│           ├── hash_map.py
│           └── min_heap.py
└── tests
    ├── conftest.py
    └── test_required_behavior.py
```

- `src/main.py`: CLI 엔트리 포인트
- `src/mini_redis/cli`: 명령 파싱과 REPL
- `src/mini_redis/core/store.py`: Redis 명령 실행, 메모리 관리, LRU, TTL 처리
- `src/mini_redis/data_structures`: 직접 구현한 해시맵, 이중 연결 리스트, 최소 힙
- `tests`: 요구사항 중심 pytest 테스트

## 지원 명령어

- `SET <key> <value>`: 문자열 값을 저장합니다. 기존 키를 덮어쓰면 TTL은 초기화됩니다.
- `GET <key>`: 값을 조회하고 성공 시 LRU 순서를 갱신합니다.
- `DEL <key>`: 키를 삭제합니다.
- `EXISTS <key>`: 키 존재 여부를 반환합니다.
- `DBSIZE`: 현재 저장된 키 개수를 반환합니다.
- `KEYS`: 전체 키 목록을 출력합니다.
- `CONFIG SET maxmemory <bytes>`: 최대 메모리를 바이트 단위로 설정합니다. `0`은 무제한입니다.
- `INFO memory`: `used_memory`, `maxmemory`, `evicted_keys`를 출력합니다.
- `EXPIRE <key> <seconds>`: 키 만료 시간을 설정합니다.
- `TTL <key>`: 남은 TTL을 조회합니다.

명령어 이름은 대소문자를 구분하지 않습니다. 공백이 있는 값은 큰따옴표로 감쌀 수 있습니다.

## 사용 예시

```text
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
mini-redis> KEYS
1. "user:2"
2. "user:3"
mini-redis> EXPIRE user:2 3
(integer) 1
mini-redis> TTL user:2
(integer) 2
```

## 메모리와 LRU

`used_memory`는 과제 기준에 맞춰 `len(utf8(key)) + len(utf8(value))`의 합으로 계산합니다. 노드, 포인터, 버킷 같은 자료구조 오버헤드는 포함하지 않습니다.

`maxmemory`가 `0`보다 크고 `SET` 이후 `used_memory`가 제한을 넘으면, 이중 연결 리스트의 꼬리부터 가장 오래 사용되지 않은 키를 제거합니다. `SET`과 성공한 `GET`은 해당 키를 리스트의 앞으로 이동시켜 최근 사용으로 표시합니다.

## TTL

TTL은 `(expire_at, key)` 형태의 항목을 최소 힙에 넣어 가장 빨리 만료될 키를 빠르게 찾습니다. 같은 키에 TTL이 여러 번 설정될 수 있으므로, 실제 삭제 시점에 해시맵에 저장된 최신 만료 시각과 힙 항목을 비교하는 lazy deletion 방식을 사용합니다.

## 해시 알고리즘

해시맵은 Python `dict` 대신 직접 구현한 체이닝 해시맵을 사용합니다. 해시 함수는 실제 해시 테이블 구현 예제로 널리 쓰이는 비암호학적 해시인 `FNV-1a 64-bit`를 사용합니다.

```text
hash = 14695981039346656037
for each byte:
    hash = hash XOR byte
    hash = (hash * 1099511628211) mod 2^64
```

예를 들어 키가 `"cat"`이면 UTF-8 바이트는 `99`, `97`, `116`입니다.

```text
초기값: 14695981039346656037
'c'(99):  hash = (초기값 XOR 99) * 1099511628211 mod 2^64
'a'(97):  hash = (이전값 XOR 97) * 1099511628211 mod 2^64
't'(116): hash = (이전값 XOR 116) * 1099511628211 mod 2^64
최종값:   17718013163177550631
```

버킷 수가 `8`개라면 `17718013163177550631 % 8 = 7`이므로 `"cat"`은 7번 버킷에 저장됩니다. 충돌이 나면 같은 버킷의 이중 연결 리스트에 엔트리를 연결하는 체이닝 방식으로 해결하며, 로드 팩터가 `0.75`를 초과하면 버킷 수를 2배로 늘려 재배치합니다.
