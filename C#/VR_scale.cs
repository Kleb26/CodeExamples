using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Valve.VR;

public class VR_scale : MonoBehaviour
{
    // Start is called before the first frame update
    public SteamVR_Action_Vector2 trackpad_pos_action;
    public float speed = 0.1f;
    private GameObject mode_obj;
    private State mode_void;
    private Vector3 init_scale;
    private Vector3 reset_scale;

    public Vector3 saved_scale;

    private void Start()
    {
        mode_obj = GameObject.Find("Control_State");
        GameObject Slice = GameObject.Find("Plane front");
        GameObject Slice0 = GameObject.Find("Slice (0)");

        mode_void = mode_obj.GetComponent<State>();
        float numOslices = mode_void.numberOfSlices;

        Plane_Position_Initialize spacing_void = Slice0.GetComponent<Plane_Position_Initialize>();
        float spacing = spacing_void.space;

        init_scale = Slice.transform.localScale;
        //take into account plane vs cube scaling (planes bigger)
        init_scale.x = init_scale.x * 10;
        init_scale.y = init_scale.z * 10;
        //Note z and y need swapping because planes are dumb
        init_scale.z = numOslices * spacing;

        //Store original dims for reset
        reset_scale = Slice0.transform.localScale;
        saved_scale = reset_scale;
        
    }

    void Update()
    {
        //Get Control mode from State script
        mode_void = mode_obj.GetComponent<State>();
        int mode = mode_void.mode;

        //cubic power for fine and coarse control
        int power = 3;
        
        if (mode == 1)
        {
            //Global scaling, hold left trigger
            if( SteamVR_Input._default.inActions.GrabPinch.GetState(SteamVR_Input_Sources.LeftHand) )
            {
                Vector2 either = trackpad_pos_action.GetAxis(SteamVR_Input_Sources.Any);

                Vector3 uniform = new Vector3(Mathf.Pow(either.y, power)*init_scale.x, 
                    Mathf.Pow(either.y, power)*init_scale.y, 
                    Mathf.Pow(either.y, power)*init_scale.z);
                transform.localScale = transform.localScale + uniform * speed;

                //Reset scale for all axes
                if( SteamVR_Input._default.inActions.GrabGrip.GetStateDown(SteamVR_Input_Sources.LeftHand))
                {
                    transform.localScale = reset_scale;
                }
                if (SteamVR_Input._default.inActions.GrabGrip.GetLastStateDown(SteamVR_Input_Sources.RightHand))
                {
                    transform.localScale = saved_scale;
                }
            }
            else
            {
                //Reset individual axes by holding right trigger (grip is bad)
                if (SteamVR_Input._default.inActions.GrabPinch.GetState(SteamVR_Input_Sources.RightHand))
                {
                    //Reset 'x'
                    if (SteamVR_Input._default.inActions.ClickRight.GetStateDown(SteamVR_Input_Sources.RightHand))
                    {
                        Vector3 scale_current = transform.localScale;
                        transform.localScale = new Vector3(reset_scale.x, scale_current.y, scale_current.z);
                    }
                    if (SteamVR_Input._default.inActions.ClickLeft.GetStateDown(SteamVR_Input_Sources.RightHand))
                    {
                        Vector3 scale_current = transform.localScale;
                        transform.localScale = new Vector3(reset_scale.x, scale_current.y, scale_current.z);
                    }

                    //Reset 'y'
                    if (SteamVR_Input._default.inActions.ClickUp.GetStateDown(SteamVR_Input_Sources.RightHand))
                    {
                        Vector3 scale_current = transform.localScale;
                        transform.localScale = new Vector3(scale_current.x, reset_scale.y, scale_current.z);
                    }
                    if (SteamVR_Input._default.inActions.ClickDown.GetStateDown(SteamVR_Input_Sources.RightHand))
                    {
                        Vector3 scale_current = transform.localScale;
                        transform.localScale = new Vector3(scale_current.x, reset_scale.y, scale_current.z);
                    }

                    //Reset 'z', i.e. into stack
                    if (SteamVR_Input._default.inActions.ClickUp.GetStateDown(SteamVR_Input_Sources.LeftHand))
                    {
                        Vector3 scale_current = transform.localScale;
                        transform.localScale = new Vector3(scale_current.x, scale_current.y, reset_scale.z);
                    }
                    if (SteamVR_Input._default.inActions.ClickDown.GetStateDown(SteamVR_Input_Sources.LeftHand))
                    {
                        Vector3 scale_current = transform.localScale;
                        transform.localScale = new Vector3(scale_current.x, scale_current.y, reset_scale.z);
                    }
                }
                else
                {
                    //Individual scale axes when not holding trigger
                    Vector2 Horizontal = trackpad_pos_action.GetAxis(SteamVR_Input_Sources.RightHand);
                    Vector2 Vertical = trackpad_pos_action.GetAxis(SteamVR_Input_Sources.LeftHand);

                    Vector3 movement = new Vector3(Mathf.Pow(Horizontal.x, power) * init_scale.x
                        , Mathf.Pow(Horizontal.y, power) * init_scale.y
                        , Mathf.Pow(Vertical.y, power) * init_scale.z);
                    transform.localScale = transform.localScale + movement * speed;

                    if(SteamVR_Input._default.inActions.GrabGrip.GetStateDown(SteamVR_Input_Sources.Any))
                    {
                        saved_scale = transform.localScale;
                        
                    }
                }

            }
            
        }
    }

}

