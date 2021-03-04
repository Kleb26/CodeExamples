using System.Collections;
using System.Collections.Generic;
using UnityEngine.UI;
using UnityEngine;
using Valve.VR;

public class State : MonoBehaviour
{
    public int mode=0;
    //Number of modes
    public int limit = 3;
    public Text mode_Text;
    public int slice_num = 0;
    //Number of slices
    public int numberOfSlices;
    public float speed;
    private float slice_float;

    public bool[] invisible_slices;
    private int lower_visible;
    private int upper_visible;
    private bool selected_visible;

    public Text slice_num_text;
    public Text range_text;

    public SteamVR_Action_Vector2 trackpad;


    private void Start()
    {
        //Initialize settings and text
        mode_Text.text = "Translate";
        slice_num = 0;
        slice_float = 0.0f;

        //initialise bool array. note all false on creation
        invisible_slices = new bool[numberOfSlices];
        //initialize limtis on visible slices
        lower_visible = 0;
        upper_visible = numberOfSlices - 1;

        selected_visible = true;
    }

    void Update()
    {
        //Cycle through modes via menu button changing text and 'mode' variable
        if(SteamVR_Input._default.inActions.Toggle.GetStateDown(SteamVR_Input_Sources.Any) )
        {
            mode = mode + 1;
            if( mode == limit)
            {
                mode = 0;
                mode_Text.text = "Translate";
            }

            if(mode==1)
            {
                mode_Text.text = "Scale";
            }

            if(mode==2)
            {
                mode_Text.text = "Slice Selector";
            }

        }

        //Whilst in slice select mode this code controls selection of the slice;
        //'slice_selector' takes the value from here and controls the movement of that slice.
        if(mode == 2)
        {
            //since the selected slice is always made visible after new selection taken
            //here the previously selected slice needs to be made invisible again
            if(slice_num<lower_visible)
            {
                invisible_slices[slice_num] = true;
            }
            if (slice_num > upper_visible)
            {
                invisible_slices[slice_num] = true;
            }

            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            //Click based discrete slice cycle
            if (SteamVR_Input._default.inActions.ClickUp.GetStateDown(SteamVR_Input_Sources.LeftHand))
            {
                slice_num = slice_num + 1;
                //Ensure to update float value too so 2 control methods don't desync
                slice_float = slice_num;
            }
        
            if(SteamVR_Input._default.inActions.ClickDown.GetStateDown(SteamVR_Input_Sources.LeftHand))
            {
                slice_num = slice_num - 1;
                slice_float = slice_num;
            }


            Vector2 Vertical = trackpad.GetAxis(SteamVR_Input_Sources.RightHand);
            //Power 5 needed for far superior coarse adjustment whilst retaining single slice fine adjustment
            int p = 5;
            float y = Vertical.y;

            //Split into positive and negative cases to remove 'dead-zone' in x**5 function near 0 due to quantisation of function
            if (y > 0)
            {
                //To allow fine/slow adjustment float value is needed since discrete values are updating too quickly when
                //done every frame.
                slice_float = slice_float + speed * Mathf.Pow(Vertical.y + 0.5f, p);
                //Must be converted to int though since slices are quantised.
                slice_num = Mathf.RoundToInt(slice_float);
            }
            if (y < 0)
            {
               slice_float = slice_float + speed * Mathf.Pow(Vertical.y - 0.5f, p);
               slice_num = Mathf.RoundToInt(slice_float);
            }

            //Enable cycling
            if (slice_num >= numberOfSlices)
            {
                slice_num = 0;
                slice_float = 0.0f;
            }
            if (slice_num < 0)
            {
                slice_num = numberOfSlices - 1;
                slice_float = numberOfSlices - 1;
            }

            slice_num_text.fontSize = 20;
            slice_num_text.text = slice_num.ToString();

            //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            //choose to toggle hide the selected slice
            if (SteamVR_Input._default.inActions.GrabPinch.GetStateDown(SteamVR_Input_Sources.LeftHand))
            {
                if(selected_visible)
                {
                    selected_visible = false;
                }
                else
                {
                    selected_visible = true;
                }
            }

            
            if(SteamVR_Input._default.inActions.GrabPinch.GetState(SteamVR_Input_Sources.LeftHand))
            {
                //reset visible slices by holding left trig and pressing either grip
                if (SteamVR_Input._default.inActions.GrabGrip.GetLastStateDown(SteamVR_Input_Sources.Any))
                {
                    Reset_invisible_slices();
                }
            }
            else
            {
                //Set limits on visible range based off grip presses.
                if (SteamVR_Input._default.inActions.GrabGrip.GetStateDown(SteamVR_Input_Sources.LeftHand))
                {
                    lower_visible = slice_num;
                    Set_invisible(lower_visible, upper_visible);
                }
                if (SteamVR_Input._default.inActions.GrabGrip.GetStateDown(SteamVR_Input_Sources.RightHand))
                {
                    upper_visible = slice_num;
                    Set_invisible(lower_visible, upper_visible);
                }
            }
            
            //make selected slice always visible, even outside the range; unless otherwise desired
            if(selected_visible)
            {
                invisible_slices[slice_num] = false;
            }

            //If a range is selected display the range above the right controller.
            if(lower_visible == 0 && upper_visible == numberOfSlices - 1)
            {
                range_text.text = "";
            }
            else
            {
                range_text.text = "[ " + lower_visible.ToString() + ", " + upper_visible.ToString() + " ]";
            }

        }
        if(mode==0)
        {
            //Display 'none' in text to indicate lack of functionality in mode 1.
            slice_num_text.fontSize = 20;
            slice_num_text.text = "none";
        }

    }

    private void Set_invisible(int lower, int upper)
    {
        int i = 0;
        while (i < lower)
        {
            invisible_slices[i] = true;
            i = i + 1;
        }
        while (i <= upper)
        {
            invisible_slices[i] = false;
            i = i + 1;
        }
        while ( i < numberOfSlices)
        {
            invisible_slices[i] = true;
            i = i + 1;
        }
    }

    private void Reset_invisible_slices()
    {
        invisible_slices = new bool[numberOfSlices];
        lower_visible = 0;
        upper_visible = numberOfSlices - 1;
    }

}
