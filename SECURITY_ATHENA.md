# AWS Athena Query Runner - Security Documentation

## Overview
The SQL Athena Query Runner module implements multiple layers of security to prevent SQL injection attacks, unauthorized access, and abuse.

## Security Features

### 1. SQL Injection Prevention

#### Comprehensive Keyword Blocking
The system blocks all dangerous SQL operations:
- **Data Modification**: DROP, DELETE, TRUNCATE, INSERT, UPDATE
- **Schema Modification**: ALTER, CREATE, RENAME
- **Access Control**: GRANT, REVOKE
- **Database Operations**: USE, EXEC, EXECUTE
- **System Commands**: SHUTDOWN, KILL
- **File Operations**: LOAD, OUTFILE, DUMPFILE, LOAD_FILE

#### Pattern-Based Detection
Multiple regex patterns detect common SQL injection techniques:
- Stacked queries (`; DROP TABLE`, `; DELETE FROM`)
- SQL comments (`--`, `/* */`)
- System variables (`@@`)
- Union-based injection (`UNION SELECT`)
- Boolean-based injection (`OR 1=1`, `AND 1=1`)
- Extended stored procedures (`xp_cmdshell`)
- Timing attacks (`BENCHMARK`, `SLEEP`, `WAITFOR DELAY`)

#### Identifier Sanitization
Database and table names are sanitized to only allow:
- Alphanumeric characters (a-z, A-Z, 0-9)
- Underscores (_)
- Hyphens (-)

This prevents SQL injection through identifier names.

#### Query Type Enforcement
Only the following query types are allowed:
- SELECT statements
- SHOW statements (e.g., SHOW TABLES, SHOW DATABASES)
- DESCRIBE statements

All other query types are blocked.

#### Multiple Statement Prevention
The system prevents stacked queries by:
1. Removing string literals
2. Counting semicolons
3. Allowing only 0 or 1 semicolon (at the end)

### 2. Rate Limiting

**Protection against abuse and DoS attacks:**
- Maximum 10 queries per minute per user
- Tracked per user ID
- Automatic cleanup of old entries
- Returns HTTP 429 (Too Many Requests) when exceeded

### 3. Query Size Limits

**Resource exhaustion prevention:**
- Maximum query length: 10,000 characters
- Maximum results returned: 1,000 rows
- Query timeout: 2 minutes

### 4. Authentication & Authorization

**All endpoints require authentication:**
- JWT token-based authentication
- User must be logged in to execute queries
- Inactive users are automatically blocked
- Token validation on every request

### 5. Audit Logging

**Complete audit trail:**
- User ID and username logged for each query
- Timestamp of execution
- Query preview (first 200 characters)
- Success/failure status
- Error messages
- Blocked attempts logged with reason

Logs are written to application logs and can be integrated with SIEM systems.

### 6. Input Validation

**Pydantic validators:**
- Query cannot be empty
- Query length validation
- Database name validation
- Automatic whitespace trimming

## Attack Scenarios Prevented

### 1. Classic SQL Injection
**Attack:** `SELECT * FROM users WHERE id = 1; DROP TABLE users; --`
**Prevention:** Semicolon in middle of query detected, multiple statements blocked

### 2. Union-Based Injection
**Attack:** `SELECT * FROM products UNION SELECT password FROM users`
**Prevention:** UNION SELECT pattern detected and blocked

### 3. Boolean-Based Blind Injection
**Attack:** `SELECT * FROM products WHERE id = 1 OR 1=1`
**Prevention:** `OR 1=1` pattern detected and blocked

### 4. Time-Based Blind Injection
**Attack:** `SELECT * FROM users WHERE id = 1 AND SLEEP(5)`
**Prevention:** SLEEP function pattern detected and blocked

### 5. Database Name Injection
**Attack:** `/tables/mydb; DROP DATABASE mydb`
**Prevention:** Identifier sanitization rejects semicolons and SQL keywords

### 6. Comment-Based Injection
**Attack:** `SELECT * FROM users WHERE id = 1 --' OR '1'='1`
**Prevention:** SQL comments (`--`) detected and blocked

### 7. Stacked Queries
**Attack:** `SELECT * FROM users; DELETE FROM users WHERE 1=1`
**Prevention:** Multiple semicolons detected, query rejected

### 8. Data Exfiltration via OUTFILE
**Attack:** `SELECT * FROM users INTO OUTFILE '/tmp/users.txt'`
**Prevention:** OUTFILE keyword blocked

## Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Athena Configuration
ATHENA_DATABASE=your_database
ATHENA_OUTPUT_LOCATION=s3://your-bucket/athena-results/
ATHENA_WORKGROUP=primary
```

### Security Constants
Defined in `backend/athena_routes.py`:
```python
MAX_QUERY_LENGTH = 10000          # Maximum query characters
MAX_RESULTS = 1000                # Maximum rows returned
QUERY_TIMEOUT_SECONDS = 120       # Query timeout (2 minutes)
MAX_QUERIES_PER_MINUTE = 10       # Rate limit per user
```

## Best Practices for Administrators

### 1. AWS IAM Permissions
Limit Athena IAM permissions to read-only access:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StartQueryExecution",
        "athena:ListDatabases",
        "athena:ListTableMetadata"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket/*",
        "arn:aws:s3:::your-bucket"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Network Security
- Deploy behind a firewall
- Use VPC endpoints for AWS services
- Enable HTTPS only
- Implement IP whitelisting if needed

### 3. Monitoring
- Monitor application logs for blocked queries
- Set up alerts for repeated SQL injection attempts
- Track query execution times
- Monitor AWS Athena costs

### 4. User Education
- Train users on proper SQL query syntax
- Provide example queries
- Document allowed query types
- Explain rate limits

## Testing Security

### Penetration Testing Checklist
- [ ] Test SQL injection with various payloads
- [ ] Test rate limiting (send >10 queries/minute)
- [ ] Test query size limits (send 10,001 character query)
- [ ] Test identifier injection (database/table names)
- [ ] Test multiple statement execution
- [ ] Test unauthorized access (no token)
- [ ] Test expired/invalid tokens
- [ ] Verify audit logs are created

### Sample Attack Payloads for Testing
```sql
-- Should all be BLOCKED:
SELECT * FROM users; DROP TABLE users;
SELECT * FROM users WHERE 1=1 OR 1=1
SELECT * FROM users UNION SELECT * FROM passwords
SELECT * FROM users; DELETE FROM users WHERE 1=1
SELECT * FROM users -- comment out rest
SELECT @@version
SELECT * INTO OUTFILE '/tmp/data.txt' FROM users
SELECT SLEEP(10)
```

## Compliance

This implementation helps meet security requirements for:
- OWASP Top 10 (SQL Injection - A03:2021)
- PCI DSS Requirement 6.5.1 (Injection Flaws)
- GDPR Article 32 (Security of Processing)
- SOC 2 Type II (Security & Availability)

## Future Enhancements

Potential improvements for even stronger security:
1. Query result encryption
2. Column-level access control
3. Query cost limits (based on data scanned)
4. IP-based rate limiting
5. Two-factor authentication for sensitive queries
6. Database activity monitoring integration
7. Anomaly detection using ML
8. Query result data masking (PII protection)

## Support

For security concerns or to report vulnerabilities:
- Contact your security team
- Review application logs
- Check AWS CloudTrail for Athena API calls

## Version History

- **v1.0** - Initial release with comprehensive SQL injection prevention
  - Multi-layer security validation
  - Rate limiting
  - Audit logging
  - Identifier sanitization
