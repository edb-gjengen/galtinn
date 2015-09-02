User
====

.. http:get:: /api/users/


    List of registered users

    **Example request**:

    .. sourcecode:: http

        GET /api/users/

    :statuscode 200: OK
    :statuscode 403: User does not have necessary permissions.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        [
            {
                "city" : "Oslo",
                "country" : "Norway",
                "postal_code" : 0266,
                "street_address" : "Odins gate 12A",
                "created" : "2013-05-22T21:58:44",
                "date_of_birth" : null,
                "email" : "robert.kolner@gmail.com",
                "first_name" : "",
                "id" : 1,
                "last_name" : "",
                "legacy_id" : null,
                "phone_number" : 90567268,
                "resource_uri" : "/api/users/1/",
                "updated" : "2013-05-22T21:58:44",
                "username" : "robert"
            }
        ]