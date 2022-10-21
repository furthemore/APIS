## fm_eventmanager's ER Diagram

```mermaid
erDiagram
LogEntry{
AutoField id
DateTimeField action_time
TextField object_id
CharField object_repr
PositiveSmallIntegerField action_flag
TextField change_message
}
Permission{
AutoField id
CharField name
CharField codename
}
Group{
AutoField id
CharField name
}
User{
AutoField id
CharField password
DateTimeField last_login
BooleanField is_superuser
CharField username
CharField first_name
CharField last_name
CharField email
BooleanField is_staff
BooleanField is_active
DateTimeField date_joined
}
ContentType{
AutoField id
CharField app_label
CharField model
}
Session{
CharField session_key
TextField session_data
DateTimeField expire_date
}
Site{
AutoField id
CharField domain
CharField name
}
U2FKey{
AutoField id
DateTimeField created_at
DateTimeField last_used_at
TextField public_key
TextField key_handle
TextField app_id
}
BackupCode{
AutoField id
CharField code
}
TOTPDevice{
AutoField id
DateTimeField created_at
DateTimeField last_used_at
BinaryField key
PositiveIntegerField last_t
}
HoldType{
AutoField id
CharField name
}
ShirtSizes{
AutoField id
CharField name
}
Discount{
AutoField id
CharField codeName
IntegerField percentOff
DecimalField amountOff
DateTimeField startDate
DateTimeField endDate
TextField notes
BooleanField oneTime
IntegerField used
CharField reason
}
PriceLevelOption{
AutoField id
CharField optionName
DecimalField optionPrice
CharField optionExtraType
CharField optionExtraType2
CharField optionExtraType3
FileField optionImage
BooleanField required
BooleanField active
IntegerField rank
TextField description
}
PriceLevel{
AutoField id
CharField name
TextField description
DecimalField basePrice
DateTimeField startDate
DateTimeField endDate
BooleanField public
TextField notes
TextField group
BooleanField emailVIP
CharField emailVIPEmails
BooleanField isMinor
}
Charity{
AutoField id
CharField name
CharField url
DecimalField donations
}
Venue{
AutoField id
CharField name
CharField address
CharField city
CharField state
CharField country
CharField postalCode
CharField website
}
Event{
AutoField id
CharField name
DateTimeField dealerRegStart
DateTimeField dealerRegEnd
DateTimeField staffRegStart
DateTimeField staffRegEnd
DateTimeField attendeeRegStart
DateTimeField attendeeRegEnd
DateTimeField onsiteRegStart
DateTimeField onsiteRegEnd
DateField eventStart
DateField eventEnd
BooleanField default
BooleanField allowOnlineMinorReg
BooleanField collectAddress
BooleanField collectBillingAddress
CharField registrationEmail
CharField staffEmail
CharField dealerEmail
CharField badgeTheme
CharField codeOfConduct
DecimalField donations
}
TableSize{
AutoField id
CharField name
TextField description
IntegerField chairMin
IntegerField chairMax
IntegerField tableMin
IntegerField tableMax
IntegerField partnerMin
IntegerField partnerMax
DecimalField basePrice
}
Department{
AutoField id
CharField name
BooleanField volunteerListOk
}
TempToken{
AutoField id
CharField token
CharField email
DateTimeField validUntil
BooleanField used
DateTimeField usedDate
BooleanField sent
}
Attendee{
AutoField id
CharField firstName
CharField preferredName
CharField lastName
CharField address1
CharField address2
CharField city
CharField state
CharField country
CharField postalCode
CharField phone
CharField email
DateField birthdate
BooleanField emailsOk
BooleanField surveyOk
BooleanField volunteerContact
CharField volunteerDepts
TextField notes
CharField parentFirstName
CharField parentLastName
CharField parentPhone
CharField parentEmail
BooleanField aslRequest
}
Badge{
AutoField id
DateTimeField registeredDate
CharField registrationToken
CharField badgeName
IntegerField badgeNumber
BooleanField printed
IntegerField printCount
FileField signature_svg
FileField signature_bitmap
}
Staff{
AutoField id
CharField registrationToken
CharField title
CharField twitter
CharField telegram
BooleanField timesheetAccess
TextField notes
TextField specialSkills
TextField specialFood
TextField specialMedical
CharField contactName
CharField contactPhone
CharField contactRelation
BooleanField needRoom
CharField gender
BooleanField checkedIn
}
Dealer{
AutoField id
CharField registrationToken
BooleanField approved
IntegerField tableNumber
TextField notes
CharField businessName
CharField website
TextField description
CharField license
BooleanField needPower
BooleanField needWifi
BooleanField wallSpace
CharField nearTo
CharField farFrom
IntegerField chairs
IntegerField tables
BooleanField reception
BooleanField artShow
TextField charityRaffle
BooleanField agreeToRules
BooleanField breakfast
BooleanField willSwitch
TextField partners
CharField buttonOffer
DecimalField discount
CharField discountReason
BooleanField emailed
BooleanField asstBreakfast
CharField logo
}
DealerAsst{
AutoField id
CharField registrationToken
CharField name
CharField email
CharField license
BooleanField sent
BooleanField paid
}
Cart{
AutoField id
CharField token
CharField form
TextField formData
TextField formHeaders
DateTimeField enteredDate
DateTimeField transferedDate
}
Order{
AutoField id
DecimalField total
CharField status
CharField reference
DateTimeField createdDate
DateTimeField settledDate
DecimalField orgDonation
DecimalField charityDonation
TextField notes
CharField billingName
CharField billingAddress1
CharField billingAddress2
CharField billingCity
CharField billingState
CharField billingCountry
CharField billingPostal
CharField billingEmail
CharField billingType
CharField lastFour
TextField apiData
UUIDField onsite_reference
}
OrderItem{
AutoField id
CharField enteredBy
DateTimeField enteredDate
}
AttendeeOptions{
AutoField id
CharField optionValue
CharField optionValue2
CharField optionValue3
}
BanList{
AutoField id
CharField firstName
CharField lastName
CharField email
TextField reason
}
Firebase{
AutoField id
CharField token
CharField name
BooleanField closed
BooleanField cashdrawer
CharField printer_url
CharField background_color
CharField foreground_color
CharField webview
}
Cashdrawer{
AutoField id
DateTimeField timestamp
CharField action
DecimalField total
DecimalField tendered
}
ReservedBadgeNumbers{
AutoField id
IntegerField badgeNumber
TextField notes
}
LogEntry||--|{User : user
LogEntry||--|{ContentType : content_type
Permission}|--|{Group : group
Permission}|--|{User : user
Permission||--|{ContentType : content_type
Group}|--|{User : user
Group}|--|{Permission : permissions
User||--|{LogEntry : logentry
User||--|{U2FKey : u2f_keys
User||--|{BackupCode : backup_codes
User||--|{TOTPDevice : totp_devices
User||--|{Cashdrawer : cashdrawer
User}|--|{Group : groups
User}|--|{Permission : user_permissions
ContentType||--|{LogEntry : logentry
ContentType||--|{Permission : permission
U2FKey||--|{User : user
BackupCode||--|{User : user
TOTPDevice||--|{User : user
HoldType||--|{Attendee : attendee
ShirtSizes||--|{Staff : staff
Discount||--|{Event : newStaffEvent
Discount||--|{Event : staffEvent
Discount||--|{Event : dealerEvent
Discount||--|{Event : assistantEvent
Discount||--|{Order : order
PriceLevelOption}|--|{PriceLevel : pricelevel
PriceLevelOption||--|{AttendeeOptions : attendeeoptions
PriceLevel||--|{OrderItem : orderitem
PriceLevel||--|{ReservedBadgeNumbers : reservedbadgenumbers
PriceLevel}|--|{PriceLevelOption : priceLevelOptions
Charity||--|{Event : event
Venue||--|{Event : event
Event||--|{TableSize : tablesize
Event||--|{Badge : badge
Event||--|{Staff : staff
Event||--|{Dealer : dealer
Event||--|{DealerAsst : dealerasst
Event||--|{ReservedBadgeNumbers : reservedbadgenumbers
Event||--|{Venue : venue
Event||--|{Discount : newStaffDiscount
Event||--|{Discount : staffDiscount
Event||--|{Discount : dealerDiscount
Event||--|{Discount : assistantDiscount
Event||--|{Charity : charity
TableSize||--|{Dealer : dealer
TableSize||--|{Event : event
Department||--|{Staff : staff
Attendee||--|{Attendee : attendee
Attendee||--|{Badge : badge
Attendee||--|{Staff : staff
Attendee||--|{Dealer : dealer
Attendee||--|{DealerAsst : dealerasst
Attendee||--|{HoldType : holdType
Attendee||--|{Attendee : parent
Badge||--|{OrderItem : orderitem
Badge||--|{Attendee : attendee
Badge||--|{Event : event
Staff||--|{Staff : staff
Staff||--|{Attendee : attendee
Staff||--|{Department : department
Staff||--|{Staff : supervisor
Staff||--|{ShirtSizes : shirtsize
Staff||--|{Event : event
Dealer||--|{DealerAsst : dealerasst
Dealer||--|{Attendee : attendee
Dealer||--|{TableSize : tableSize
Dealer||--|{Event : event
DealerAsst||--|{Dealer : dealer
DealerAsst||--|{Attendee : attendee
DealerAsst||--|{Event : event
Order||--|{OrderItem : orderitem
Order||--|{Discount : discount
OrderItem||--|{AttendeeOptions : attendeeoptions
OrderItem||--|{Order : order
OrderItem||--|{Badge : badge
OrderItem||--|{PriceLevel : priceLevel
AttendeeOptions||--|{PriceLevelOption : option
AttendeeOptions||--|{OrderItem : orderItem
Firebase||--|{Cashdrawer : firebase_cashdrawer
Cashdrawer||--|{User : user
Cashdrawer||--|{Firebase : position
ReservedBadgeNumbers||--|{Event : event
ReservedBadgeNumbers||--|{PriceLevel : priceLevel
```
