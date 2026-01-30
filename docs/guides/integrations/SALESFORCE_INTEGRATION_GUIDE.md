# Salesforce Integration Guide for Eniscope Core API

## Executive Summary

Based on the Core API v1 documentation, this guide provides the **recommended architecture** for integrating Eniscope energy metering data with Salesforce.

## API Overview

- **Base URL**: `https://core.eniscope.com/`
- **Authentication**: Basic Auth (email + MD5 password hash) + API Key header
- **Protocol**: HTTPS REST API (no VPN/mTLS required)
- **Rate Limits**: POST limited to 1000 rows, PUT limited to 100 rows per request

## Recommended Integration Architecture

### **Option 1: Salesforce-Native Integration (Recommended for Most Cases)**

**Best For**: 
- Real-time or near-real-time data access from Salesforce
- On-demand lookups (e.g., "Get latest energy usage" buttons)
- Small to medium data volumes

**Architecture**:
```
Salesforce → Named Credential → Eniscope Core API
```

**Implementation Steps**:

1. **Create Named Credential in Salesforce**
   - Setup → Named Credentials → New
   - URL: `https://core.eniscope.com`
   - Identity Type: Named Principal
   - Authentication Protocol: Password Authentication
   - Store username/password securely
   - Add custom header: `X-Eniscope-API: {your-api-key}`

2. **Create Apex Classes for API Integration**

   ```apex
   public class EniscopeAPIService {
       private static final String NAMED_CREDENTIAL = 'Eniscope_API';
       private static String sessionToken;
       
       // Authenticate and get session token
       private static void authenticate() {
           HttpRequest req = new HttpRequest();
           req.setEndpoint('callout:' + NAMED_CREDENTIAL + '/v1/1/organizations');
           req.setMethod('GET');
           
           Http http = new Http();
           HttpResponse res = http.send(req);
           
           // Extract token from response headers
           sessionToken = res.getHeader('X-Eniscope-Token');
       }
       
       // Get organizations
       public static List<Organization> getOrganizations() {
           if (sessionToken == null) authenticate();
           
           HttpRequest req = new HttpRequest();
           req.setEndpoint('callout:' + NAMED_CREDENTIAL + '/v1/1/organizations');
           req.setMethod('GET');
           req.setHeader('X-Eniscope-Token', sessionToken);
           
           Http http = new Http();
           HttpResponse res = http.send(req);
           
           return (List<Organization>) JSON.deserialize(
               res.getBody(), 
               List<Organization>.class
           );
       }
       
       // Get devices for an organization
       public static List<Device> getDevices(String organizationId) {
           if (sessionToken == null) authenticate();
           
           HttpRequest req = new HttpRequest();
           req.setEndpoint('callout:' + NAMED_CREDENTIAL + 
               '/v1/1/devices?organization=' + organizationId);
           req.setMethod('GET');
           req.setHeader('X-Eniscope-Token', sessionToken);
           
           Http http = new Http();
           HttpResponse res = http.send(req);
           
           return (List<Device>) JSON.deserialize(
               res.getBody(), 
               List<Device>.class
           );
       }
       
       // Get readings for a channel
       public static ReadingData getReadings(String channelId, 
                                              String dateRange, 
                                              List<String> fields) {
           if (sessionToken == null) authenticate();
           
           String fieldsParam = String.join(fields, '&fields[]=');
           HttpRequest req = new HttpRequest();
           req.setEndpoint('callout:' + NAMED_CREDENTIAL + 
               '/v1/1/readings/' + channelId + 
               '?daterange=' + dateRange + 
               '&fields[]=' + fieldsParam + 
               '&res=3600&action=summarize');
           req.setMethod('GET');
           req.setHeader('X-Eniscope-Token', sessionToken);
           
           Http http = new Http();
           HttpResponse res = http.send(req);
           
           return (ReadingData) JSON.deserialize(
               res.getBody(), 
               ReadingData.class
           );
       }
   }
   ```

3. **Create Custom Objects in Salesforce**
   - **Energy Device** (`Energy_Device__c`)
     - Device ID (External ID)
     - Device Name
     - Organization ID (Lookup)
     - UUID
     - Device Type
     - Status
     - Registration Date
     - Expiration Date
   
   - **Energy Channel** (`Energy_Channel__c`)
     - Channel ID (External ID)
     - Channel Name
     - Device (Lookup to Energy Device)
     - Organization ID
     - Tariff ID
   
   - **Energy Reading** (`Energy_Reading__c`)
     - Reading Timestamp
     - Channel (Lookup to Energy Channel)
     - Energy (kWh)
     - Power (kW)
     - Voltage (V)
     - Current (A)
     - Other fields as needed

4. **Create Scheduled Jobs for Data Sync**
   ```apex
   global class SyncEniscopeDevices implements Schedulable {
       global void execute(SchedulableContext ctx) {
           // Sync devices and latest readings
           List<Organization> orgs = EniscopeAPIService.getOrganizations();
           for (Organization org : orgs) {
               List<Device> devices = EniscopeAPIService.getDevices(org.organizationId);
               // Upsert devices into Salesforce
               // Get channels for each device
               // Get latest readings
           }
       }
   }
   ```

5. **Create Flow/Apex Triggers for On-Demand Lookups**
   - Button on Account/Contact: "Get Latest Energy Usage"
   - Calls Eniscope API to fetch real-time data
   - Displays in Lightning Component or updates records

### **Option 2: Middleware Integration (Recommended for High Volume)**

**Best For**:
- High-volume data ingestion (1000+ readings per sync)
- Complex data transformations
- Multi-system integrations
- Need for retry logic and error handling outside Salesforce

**Architecture**:
```
Eniscope API → Middleware (AWS Lambda/Azure Functions/MuleSoft) → Salesforce REST API
```

**Implementation**:
1. **Middleware Layer** (Python/Node.js example):
   ```python
   import requests
   import hashlib
   import base64
   from simple_salesforce import Salesforce
   
   # Eniscope API Client
   class EniscopeClient:
       def __init__(self, api_key, email, password):
           self.api_key = api_key
           self.email = email
           self.password_md5 = hashlib.md5(password.encode()).hexdigest()
           self.base_url = "https://core.eniscope.com"
           self.session_token = None
       
       def authenticate(self):
           auth_string = f"{self.email}:{self.password_md5}"
           auth_b64 = base64.b64encode(auth_string.encode()).decode()
           
           headers = {
               'Authorization': f'Basic {auth_b64}',
               'X-Eniscope-API': self.api_key
           }
           
           response = requests.get(
               f"{self.base_url}/v1/1/organizations",
               headers=headers
           )
           
           self.session_token = response.headers.get('X-Eniscope-Token')
           return self.session_token
       
       def get_readings(self, channel_id, date_range='lastweek', fields=['E', 'P']):
           if not self.session_token:
               self.authenticate()
           
           params = {
               'daterange': date_range,
               'res': '3600',
               'action': 'summarize'
           }
           params.update({f'fields[]': f for f in fields})
           
           headers = {
               'X-Eniscope-Token': self.session_token,
               'X-Eniscope-API': self.api_key
           }
           
           response = requests.get(
               f"{self.base_url}/v1/1/readings/{channel_id}",
               headers=headers,
               params=params
           )
           
           return response.json()
   
   # Salesforce Integration
   def sync_to_salesforce(readings_data, sf_connection):
       for reading in readings_data:
           sf_connection.Energy_Reading__c.create({
               'Reading_Timestamp__c': reading['ts'],
               'Channel__c': reading['channelId'],
               'Energy_kWh__c': reading.get('E', 0),
               'Power_kW__c': reading.get('P', 0)
           })
   ```

2. **Schedule Middleware** (AWS EventBridge / Cron):
   - Run every 15 minutes / 1 hour
   - Fetch latest readings from Eniscope
   - Transform and upsert to Salesforce via Bulk API

### **Option 3: Platform Events (For Real-Time Updates)**

**Best For**:
- Real-time energy alerts
- Event-driven architecture
- When Eniscope can push webhooks (if supported)

**Implementation**:
1. Create Platform Event: `Energy_Alert__e`
2. Middleware listens to Eniscope webhooks (if available)
3. Publishes Platform Events to Salesforce
4. Flow/Trigger processes events

## Data Mapping Recommendations

### Core Objects Mapping

| Eniscope API | Salesforce Object | Key Fields |
|-------------|------------------|------------|
| `/organizations` | `Account` | Organization Name, Organization ID (External) |
| `/devices` | `Energy_Device__c` | Device Name, UUID, Device Type, Status |
| `/channels` | `Energy_Channel__c` | Channel Name, Device Lookup, Tariff |
| `/readings/{channelId}` | `Energy_Reading__c` | Timestamp, Energy (E), Power (P), Voltage (V) |

### Common Energy Fields to Sync

- **E** (Energy) → `Energy_kWh__c` (Number)
- **P** (Power) → `Power_kW__c` (Number)
- **V** (Voltage) → `Voltage_V__c` (Number)
- **I** (Current) → `Current_A__c` (Number)
- **PF** (Power Factor) → `Power_Factor__c` (Number)
- **T** (Temperature) → `Temperature_C__c` (Number)

## Authentication Best Practices

1. **Store Credentials Securely**:
   - Use Named Credentials (Option 1) or Protected Custom Settings
   - Never hardcode API keys in Apex
   - Rotate API keys regularly

2. **Session Token Management**:
   - Cache session token in Platform Cache (15-30 min TTL)
   - Re-authenticate on 401/419 errors
   - Use token for subsequent requests

3. **MD5 Password Hash**:
   ```apex
   String passwordHash = EncodingUtil.convertToHex(
       Crypto.generateDigest('MD5', Blob.valueOf(password))
   );
   ```

## Error Handling

Handle these HTTP status codes:
- **200**: Success
- **401/419**: Unauthorized - Re-authenticate
- **402**: Payment Required - Subscription expired
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource doesn't exist
- **429**: Too Many Requests - Rate limit exceeded (implement backoff)
- **500**: Server Error - Retry with exponential backoff

## Rate Limiting Considerations

- **POST `/dataingress/generic`**: Max 1000 rows per request
- **PUT `/dataingress/generic`**: Max 100 rows per request
- **GET requests**: No explicit limit, but use pagination (`?page=1&limit=100`)
- Implement exponential backoff for 429 responses

## Recommended Sync Frequency

- **Devices/Channels**: Daily (low change frequency)
- **Readings**: Every 15 minutes to 1 hour (depending on business needs)
- **Alarms/Events**: Real-time or every 5 minutes

## Security Considerations

1. **HTTPS Only**: All API calls use HTTPS
2. **API Key Protection**: Store in Named Credentials or Secure Storage
3. **Field-Level Security**: Restrict access to energy data fields
4. **Sharing Rules**: Control which users can see which organizations' data

## Testing Strategy

1. **Unit Tests**: Mock HTTP callouts using `Test.setMock()`
2. **Integration Tests**: Use sandbox/test API credentials
3. **Error Scenarios**: Test authentication failures, rate limits, network errors

## Next Steps

1. **Obtain API Credentials**: Contact Eniscope support for API key
2. **Choose Integration Pattern**: Option 1 (Salesforce-native) or Option 2 (Middleware)
3. **Create Custom Objects**: Set up Energy Device, Channel, and Reading objects
4. **Implement Authentication**: Set up Named Credential or middleware auth
5. **Build Sync Jobs**: Create scheduled Apex or middleware jobs
6. **Test & Deploy**: Test in sandbox, then deploy to production

## Additional Resources

- Core API Documentation: See `Core_API_v1.txt`
- Generic Ingress Instructions: See `Generic_ingress_instructions.txt`
- Salesforce HTTP Callouts: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_restful_http_httprequest.htm
- Named Credentials: https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm


