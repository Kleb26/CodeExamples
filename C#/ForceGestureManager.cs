using System.Collections;
using System.Collections.Generic;
using UnityEngine.Events;
using UnityEngine;
using Valve.VR;

public class ForceGestureManager : MonoBehaviour
{
    private Vector3 savedPos;
    private bool flag = false;
    private bool memory = false;
    private Vector3 delta;
    public static Collider RayhitCollider;
    

    public float Threshold = 2.5f;

    //Channel etiqet:
    //Channel set true by channeling ability;
    //ALL abilities check channel to know if can self cast (all abilities prevented if channel)
    //channeling abilites set private override variable if they are channeling to allow self cast whilst channel is true (BUT still MUST check for another channel first)
    //Channel reset to false when channelling ability stops.
    public static bool Channel = false;

    //Public flags. Etiqet:
    //The flags are set true here if gesture occurs; can only occur once per trigger press.
    //The flags are reset to false on trigger release press release.
    //The flags may be reset to false by an external script once the flag has been acted on.
    public static bool forwardThrust  = false;
    public static bool backwardThrust = false;
    public static bool lightning      = false;

    private void Start()
    {
        Channel = false;
    }

    private void FixedUpdate()
    {

        if (!SteamVR_Input._default.inActions.GrabPinch.GetState(SteamVR_Input_Sources.LeftHand)) //Ensure reset by doing continuously
        {
            flag = false;

            //Raycast manager
            RayhitCollider = null;

            //Reset memory; only one thrust triggerable per trigger press.
            memory = false;
            //Reset public flags in case they haven't been used.
            forwardThrust  = false;
            backwardThrust = false;
            lightning      = false;
        }


        if (SteamVR_Input._default.inActions.GrabPinch.GetState(SteamVR_Input_Sources.LeftHand)) //continuous poll on hold trigger
        {
            //Raycast Manager. Continuously poll as makes aiming easier; won't set to null, so only changes on new target (doenst impact pull)
            RaycastHit Hit;
            if (Physics.Raycast(transform.position, transform.forward, out Hit, Mathf.Infinity, 1 << 10))
            {
                RayhitCollider = Hit.collider;
            }

            if (flag) //simply delays a frame to ensure velocity exist. legacy/redundant.
            {
                delta = transform.position - savedPos;
                forwardThrust  =  forwardThrust | CheckThrust(0, 1); //OR prevents check falsing flag before read by other script.
                backwardThrust = backwardThrust | CheckThrust(0, -1);
                lightning      = SteamVR_Input._default.inActions.GrabPinch.GetState(SteamVR_Input_Sources.RightHand);
            }
            savedPos = transform.position;
            flag = true;
        }

    }

    //axis: 0 = forward, 1 = right, 2= up
    //polarity: 1 = forward, -1 = backward
    private bool CheckThrust(int axis, int polarity)
    {
        float displacement = 0f;

        switch(axis)
        {
            case 0:
                displacement = polarity * Vector3.Dot(delta, transform.forward);
                break;
            case 1:
                displacement = polarity * Vector3.Dot(delta, transform.right);
                break;
            case 2:
                displacement = polarity * Vector3.Dot(delta, transform.up);
                break;
        }

        float speed = displacement / Time.fixedDeltaTime;
        if (!memory & (speed > Threshold))
        {
            memory = true;
            return true;
        }
        else
        {
            return false;
        }

    }
}
