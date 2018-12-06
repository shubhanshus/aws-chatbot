$(document).ready(function() {
  var form = document.getElementById("chat-box");
  var submit = document.getElementById("chat-submit");
  var input = document.getElementById("chat-user");
  var container = document.getElementById("dialogue-container");
  var reply;
  var ids = 0;
  var height=0;

  var AWSconfig = {
    accessKey: "",
    secretKey: "",
    S3Bucket: "",
    region: "us-east-1",
    sessionToken: "",
    client_id: "", // removed on purpose
    client_secret: "", // removed on purpose
    user_pool_id: "", // removed on purpose
    cognito_domain_url:
      "https://restaurant-suggestions.auth.us-east-1.amazoncognito.com",
    redirect_uri: "https://s3.amazonaws.com/chatbot-assignment-2/index.html",
    identity_pool_id: "*****" // Identity pool ID
  };
  let apigClient = {};
  var getParameterByName = function(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
      results = regex.exec(url);
    if (!results[2]) return "";
    if (!results) return null;
    return decodeURIComponent(results[2].replace(/\+/g, " "));
  };
  //console.log("Code = " + getParameterByName("code"));
  var exchangeAuthCodeForCredentials = function({
    auth_code = getParameterByName("code"),
    client_id = AWSconfig.client_id,
    client_secret = AWSconfig.client_secret,
    identity_pool_id = AWSconfig.identity_pool_id,
    aws_region = AWSconfig.region,
    user_pool_id = AWSconfig.user_pool_id,
    cognito_domain_url = AWSconfig.cognito_domain_url,
    redirect_uri = AWSconfig.redirect_uri
  }) {
    return new Promise((resolve, reject) => {
      var settings = {
        url: `${cognito_domain_url}/oauth2/token`,
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "Access-Control-Allow-Origin": "*",
          Authorization: "Basic " + btoa(client_id + ":" + client_secret)
        },
        data: {
          grant_type: "authorization_code",
          client_id: client_id,
          client_secret: client_secret,
          redirect_uri: redirect_uri,
          code: auth_code
        }
      };
      $.ajax(settings).done(function(response) {
        //console.log("OAuth2 Token Call Responded");
        //console.log(response);
        if (response.id_token) {
          AWS.config.region = aws_region;
          AWS.config.credentials = new AWS.CognitoIdentityCredentials({
            IdentityPoolId: identity_pool_id,
            Logins: {
              [`cognito-idp.${aws_region}.amazonaws.com/${user_pool_id}`]: response.id_token
            }
          });
          // console.log({
          //   IdentityPoolId: identity_pool_id,
          //   Logins: {
          //     [`cognito-idp.${aws_region}.amazonaws.com/${user_pool_id}`]: response.id_token
          //   }
          // });
          AWS.config.credentials.refresh(function(error) {
            //console.log("Error", error);
            if (error) {
              reject(error);
            } else {
              //console.log("Successfully Logged In");
              resolve(AWS.config.credentials);
            }
          });
        } else {
          reject(response);
        }
      });
    });
  };
  exchangeAuthCodeForCredentials({
    auth_code: getParameterByName("code"),
    client_id: AWSconfig.client_id,
    client_secret: AWSconfig.client_secret,
    identity_pool_id: AWSconfig.identity_pool_id,
    aws_region: AWSconfig.region,
    user_pool_id: AWSconfig.user_pool_id,
    cognito_domain_url: AWSconfig.cognito_domain_url,
    redirect_uri: AWSconfig.redirect_uri
  })
    .then(function(response) {
      //console.log("Inside Then Function", response);
      apigClient = apigClientFactory.newClient({
        accessKey: response.accessKeyId,
        secretKey: response.secretAccessKey,
        sessionToken: response.sessionToken,
        region: "us-east-1",
        apiKey: "***"
      });
      apigClient.accessKey = response.accessKeyId;
      apigClient.secretKey = response.secretAccessKey;
      apigClient.sessionToken = response.sessionToken;
    })
    .catch(function(error) {
      console.log("error = " + this.error);
      console.log("response = " + this.response);
    });

  AWS.config.region = "us-east-1"; // Region
  //console.log("Access Key", apigClient.accessKey);
  //console.log("secretKey ", apigClient.secretKey);

  //console.log("Final Console Log");

  form.addEventListener("submit", function(event) {
    event.preventDefault();
    create_bubble_user();
  });

  function create_bubble_user() {
    if (input.value != "") {
      var div = document.createElement("DIV");
      var para = document.createElement("SPAN");
      var txt = document.createTextNode(input.value);
      div.setAttribute("class", "dialogue dialogue-user");
      para.appendChild(txt);
      div.appendChild(para);
      container.appendChild(div);
      get_request();
      input.value = "";
      checkHeight();
    }
  }

  function got_reply() {
    create_bubble_bot(reply);
  }

  function checkHeight(){
  $('#dialogue-container').each(function(i, value){
    height += parseInt($(this).height());
  });
  $('div').animate({scrollTop: height});
}

  function create_bubble_bot(str) {
    var div = document.createElement("DIV");
    var para = document.createElement("SPAN");
    var txt = document.createTextNode(str);
    div.setAttribute("class", "dialogue dialogue-bot");
    para.appendChild(txt);
    div.appendChild(para);
    container.appendChild(div);
    checkHeight();
  }

  function get_request() {
    var body = {
      params: {
        message: input.value,
        userId: "12345"
      }
    };

    // console.log("Access Key", apigClient.accessKey);
    // console.log("secretKey ", apigClient.secretKey);
    apigClient
      .chatbotPost({}, body)
      .then(function(result) {
        // Add success callback code here.
        reply = result.data.body["response"];
        console.log(result.data);
        got_reply();
      })
      .catch(function(result) {
        // Add error callback code here.
        console.log("Error:", result);
      });
  }
});
