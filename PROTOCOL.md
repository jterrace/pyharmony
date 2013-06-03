# Logitech Harmony Protocol

This document describes the Logitech Harmony protocol used for communicating
with the Harmony Link device.

## Harmony Link Device

The Logitech Harmony Link connects to your home wireless network and obtains an
IP address. It runs an [XMPP](http://en.wikipedia.org/wiki/XMPP) server that
listens on port 5222.

## Authentication

### Obtaining Login Token

The first step in authenticating is sending a Logitech username and password to
a Logitech web service. The endpoint for getting an authentication token is:

    https://svcs.myharmony.com/CompositeSecurityServices/Security.svc/json/GetUserAuthToken

A POST request is sent to this URL with a payload of JSON. The `Content-Type`
request header must be set to `application/json; charset=utf-8` and the body of
the request should contain JSON like this:

    {
      "password": "secret", 
      "email": "foo@example.com"
    }

The response will also be JSON of the form:

    {
      "GetUserAuthTokenResult": {
        "AccountId": 0,
        "UserAuthToken": "xyzxyz"
      }
    }

The value of `UserAuthToken` is a base64 string containing 48 bytes of data.
This token, which I will call the "Login Token", is used in the next step.

### Obtaining Session Token

Once the login token is obtained, a session token must be obtained. This is done
by logging into the Harmony device with username `guest@x.com` and password
`guest`. The login process uses the XMPP SASL PLAIN authentication standard
(XEP-0034).

Once logged in as guest, the XMPP IQ Query Action Protocol standard (XEP-0099)
is used to send an XML stanza to the server. The XML looks like this:

    <iq type="get" id="3174962747" from="guest">
      <oa xmlns="connect.logitech.com" mime="vnd.logitech.connect/vnd.logitech.pair">
        token=y6jZtSuYYOoQ2XXiU9cYovqtT+cCbcyjhWqGbhQsLV/mWi4dJVglFEBGpm08OjCW:name=1vm7ATw/tN6HXGpQcCs/A5MkuvI#iOS6.0.1#iPhone
      </oa>
    </iq>

The important part here is the content of the `<oa>` tag. It comes in the format
`token=<T>:name=<N>#<D>` where `T` is the base64-encoded Login Token, `N` is any
unique identifier (doesn't seem to matter in my tests), and `D` is a client
device description. The server appears to validate these device descriptions, as
no other value besides `iOS6.0.1#iPhone` seemed to work when I tried it. I
assume it might do some sort of validation checking for one of iPhone, Android,
etc.

After this stanza is sent, the server sends back a response that looks like:

<iq type="get" id="eef0e56c-8ceb-4c40-abf9-583ce15c2cb4-2">
    <oa xmlns="connect.logitech.com" errorcode="200" mime="vnd.logitech.connect/vnd.logitech.pair" errorstring="OK">
      identity=753b4836-2093-4c56-b4cf-eb6db9da28cb:status=succeeded
    </oa>
</iq>

The important part here is the content of the `<oa>` tag. It contains the
"identity" string, which I will call the Session Token. It is a UUID version 4
string that contains 16 bytes of information. This is what's used to login to
the device as an authenticated user.

### Logging In

Once the Session Token is obtained, it can be used to login to the harmony
device as an authenticated XMPP user. The username for logging in is
`<session_token>@x.com` and the password is `<session_token>`. Example:

    username: 764b97db-f883-4ccd-b1db-26bb9b20aee8@x.com
    password: 764b97db-f883-4ccd-b1db-26bb9b20aee8

Once logged in with this session token, commands can be sent to the device.

## Sending Commands

Once logged in with the session token, commands can be sent to the device. The
XMPP command for sending a "volume down" press event looks like this:

    <iq type="get" id="5e518d07-bcc2-4634-ba3d-c20f338d8927-2">
      <oa xmlns="connect.logitech.com" mime="vnd.logitech.harmony/vnd.logitech.harmony.engine?holdAction">
        action={"type"::"IRCommand","deviceId"::"11586428","command"::"VolumeDown"}:status=press
      </oa>
    </iq>

I have verified that this does send the volume down press event. A followup
release event would have to be sent to stop the volume from continuing to go
down. It looks like the `deviceId` parameter is some numeric identifier of the
device you're sending the command for. I assume this can be obtained from the
sync protocol but have not yet investigated.

### Retrieving devices and command list

You can send an IQ query with an `<oa>` tag to ask for `?config`:

    <iq type="get" id="2320426445" from="e01b88af-b4cd-4d1c-8e76-85562ea3fad5">
      <oa xmlns="connect.logitech.com" mime="vnd.logitech.harmony/vnd.logitech.harmony.engine?config">
      </oa>
    </iq>

The response contains a CDATA body that has a JSON string containing the list
of devices and their available commands.
