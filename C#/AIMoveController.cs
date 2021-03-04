using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class AIMoveController : MonoBehaviour
{
    public float minRad = 2f;
    public float maxRad = 10f;
    public float speed  = 0.5f;
    public float evasiveRate = 1f; //seconds
    public bool canStand = true;
    public float standupDelay = 3f; //seconds

    public bool AvoidFlag = false;

    private GameObject Player;
    private Rigidbody maBod;
    private float timer;
    private Vector3 evasiveVec;
    private Vector3 RngChngDir;

    private bool Stood = true;
    private bool inBand = true;

    private void Start()
    {
        Player = GameObject.Find("Camera");
        maBod  = gameObject.GetComponent<Rigidbody>();
        timer = 0f;
        evasiveVec = new Vector3(0f, 0f, 0f);
    }

    void Update()
    {
        float currentRad = Mathf.Abs((Player.transform.position - transform.position).magnitude);
        float deltad     = speed * Time.deltaTime;
        
        
        //Check if held via if gun works. (NOTE: if gun dont work enemy wont move)
        if (gameObject.GetComponent<EnemyGun>().GunEnabled)
        {
            //create larger trigger area avoid enemies that will trigger here causing them to keep certain distance from each other
            timer = timer + Time.deltaTime;

            if (Stood)
            {
                if (transform.up.y < 0.6)
                {
                    Stood = false;
                    timer = 0f;
                }

                if(!AvoidFlag) //Check if another enemy too close and need to avoid before normal move pattern. Detection in another script.
                    //Avoidance movement dealt with in detection script
                {
                    if (inBand && 
                    (currentRad >= minRad) &&
                    (currentRad <= maxRad)) //If correct distance band from player
                    {
                        if (timer > evasiveRate)
                        {
                            evasiveVec = Random.insideUnitSphere;
                            timer = 0f;
                        }
                        transform.position += VectorEliminateY(evasiveVec.normalized * speed * Time.deltaTime);
                    }
                    else //move into distance band
                    {
                        
                        if (currentRad < minRad)
                        {
                            inBand = false;
                            timer = 0f;
                            Vector3 PlayerDir = (Player.transform.position - transform.position).normalized;
                            RngChngDir = -1f * VectorEliminateY(PlayerDir * speed * Time.deltaTime);
                        }
                        if (currentRad > maxRad)
                        {
                            inBand = false;
                            timer = 0f;
                            Vector3 PlayerDir = (Player.transform.position - transform.position).normalized;
                            RngChngDir = VectorEliminateY(PlayerDir * speed * Time.deltaTime);
                        }
                        if(!inBand)
                        {
                            transform.position += RngChngDir;

                            if (timer > evasiveRate)
                            {
                                inBand = true;
                                timer = 0f;
                            }
                        }



                    }
                }
                else
                {
                    timer = 0f;
                }
                
            }
            else
            {
                if(timer > standupDelay)
                {
                    Quaternion standing = Quaternion.FromToRotation(transform.up, Vector3.up) * transform.rotation;
                    transform.rotation = standing;
                }
                

                if(transform.up.y > 0.95)
                {
                    Stood = true;
                    timer = 0f;
                }
            }
            
            

        }

        
        

    }

    //Public cos real useful
    public static Vector3 VectorEliminateY(Vector3 input)
    {
        return new Vector3(input.x, 0f, input.z);
    }

}
